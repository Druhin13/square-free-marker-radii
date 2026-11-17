// Independently designed exhaustive rule verifier using owner-supplied
// selected-context *data*. Does not rely on the original generator's code.
// "Independent" refers to checker implementation, not another human author.
// Prunes source words that are not lexicographically minimal in their H-orbit;
// every original source has an H-image that is minimal, and the candidate
// marker rule is H-invariant by how it is decoded.
#include <iostream>
#include <fstream>
#include <set>
#include <string>
#include <vector>
#include <array>
#include <algorithm>
#include <stdexcept>
#include <cstdint>
using namespace std;
using Perm = array<int,4>;
int r,k,nmax,w[20];
set<Perm> group;
set<uint32_t> chosen;
uint64_t visited[21]={};
uint64_t nodes = 0;

Perm compose(const Perm &p, const Perm &q) {
    Perm out;for(int x=0;x<4;x++)out[x]=p[q[x]];return out;
}
void generate_group(const string &name) {
    vector<Perm> generators;
    if(name=="S4")generators={Perm{1,0,2,3},Perm{1,2,3,0}};
    else if(name=="A4")generators={Perm{1,2,0,3},Perm{1,0,3,2}};
    else if(name=="S3")generators={Perm{1,2,0,3},Perm{1,0,2,3}};
    else if(name=="V4i")generators={Perm{1,0,2,3},Perm{0,1,3,2}};
    else throw runtime_error("Unexpected subgroup");
    group.insert(Perm{0,1,2,3});
    for(bool changed=true;changed;){
        changed=false;
        auto copy=group;
        for(auto const&p:copy)for(auto const&q:generators)
            if(group.insert(compose(p,q)).second)changed=true;
    }
}

// Reject prefixes non-minimal under any H relabeling.
bool hminimal(int n){
    for(const Perm&g:group){
        for(int i=0;i<n;i++){
            if(g[w[i]]<w[i])return false;
            if(g[w[i]]>w[i])break;
        }
    }
    return true;
}

bool square_ending_here(int n){
    for(int period=1;2*period<=n;period++){
        int i=n-2*period;
        bool same=true;
        for(int j=0;j<period;j++) if(w[i+j]!=w[i+period+j]) {same=false;break;}
        if(same)return true;
    }
    return false;
}

uint32_t canonical_orbit_context(int offset){
    uint32_t best=UINT32_MAX;
    for(const Perm&g:group){
        uint32_t value=0;
        for(int j=0;j<k;j++)value=(value<<2)|uint32_t(g[w[offset+j]]);
        if(value<best)best=value;
    }
    return best;
}

bool selected(int offset) {return chosen.count(canonical_orbit_context(offset));}
void fail(const char*reason,int n){
    cerr<<"RULE FAILURE "<<reason<<" on ";
    for(int i=0;i<n;i++){cerr<<w[i];}
    cerr<<'\n';
    throw runtime_error("Model violates full finite-source constraint");
}
void search(int n){
    visited[n]++;
    if(n==k+1 && selected(0)&&selected(1))fail("distance1",n);
    if(n==k+2 && selected(0)&&selected(2))fail("distance2",n);
    if(n==nmax){
        bool present=false;
        for(int pos=0;pos<5 && !present;pos++)present=selected(pos);
        if(!present)fail("covering",n);
        return;
    }
    for(int a=0;a<4;a++){
        w[n]=a;
        if(!square_ending_here(n+1) && hminimal(n+1))search(n+1);
    }
}

int main(int argc,char**argv){
    try{
        if(argc!=4)throw runtime_error("Expected radius subgroup selected.txt");
        r=stoi(argv[1]);if(r!=6 && r!=7)throw runtime_error("Unexpected radius");
        k=2*r+1;nmax=k+4;
        const string subgroup=argv[2];generate_group(subgroup);
        ifstream f(argv[3]);if(!f)throw runtime_error("Selected context file missing");
        string s;
        for(;f>>s;){
            if((int)s.length()!=k)throw runtime_error("Wrong context width");
            uint32_t key=0; for(char c:s){
                if(c<'0'||c>'3')throw runtime_error("Nonalphabet digit");
                key=(key<<2)|uint32_t(c-'0');
            }
            if(!chosen.insert(key).second)throw runtime_error("Duplicate chosen context");
            // Independent check that a stored key is indeed the H-minimum.
            for(const Perm&g:group){
                uint32_t candidate=0;
                for(char c:s)candidate=(candidate<<2)|uint32_t(g[c-'0']);
                if(candidate<key)throw runtime_error("Selected context not H-minimal");
            }
        }
        search(0);
        uint64_t expected_l1=0,expected_l2=0,expected_l3=0;
        size_t expected_selected=0, expected_group=0;
        if(subgroup=="S4" && r==7){
            expected_l1=453998;expected_l2=1190259;expected_l3=8180124;
            expected_selected=47142;expected_group=24;
        } else if(subgroup=="A4" && r==6){
            expected_l1=132094;expected_l2=346366;expected_l3=2380518;
            expected_selected=13611;expected_group=12;
        } else if(subgroup=="S3" && r==6){
            expected_l1=264188;expected_l2=692732;expected_l3=4761036;
            expected_selected=27586;expected_group=6;
        } else if(subgroup=="V4i" && r==6){
            expected_l1=396282;expected_l2=1039098;expected_l3=7141554;
            expected_selected=41760;expected_group=4;
        } else throw runtime_error("Unapproved radius/group combination");
        if(group.size()!=expected_group || chosen.size()!=expected_selected ||
           visited[k+1]!=expected_l1 || visited[k+2]!=expected_l2 ||
           visited[nmax]!=expected_l3)throw runtime_error("Unexpected orbit census");
        cout<<"VERIFIED "<<subgroup<<" radius="<<r<<" group-order="<<group.size()
            <<" selected-orbits="<<chosen.size()
            <<" word-counts n"<<k+1<<"="<<visited[k+1]
            <<" n"<<k+2<<"="<<visited[k+2]
            <<" n"<<nmax<<"="<<visited[nmax]<<'\n';
    }catch(const exception&e){cerr<<e.what()<<'\n';return 1;}
}
