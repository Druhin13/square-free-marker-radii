/* Independent P1.4 audit: every NAMED source word, no symmetry pruning.
 * This is deliberately not the existing C++ orbit-representative verifier.
 * Expand every selected context under a directly enumerated alphabet group
 * into a named-word bitset, then enumerate all finite square-free words
 * exhaustively and check packing/covering from their actual five windows.
 *
 * For radius seven, this checks all 196,322,976 length-19 words,
 * rather than the earlier 8,180,124 S4 orbit representatives.
 * Input file SHA-256 and expected counts are independently guarded by
 * tools/run_named_positive_audit.py and the published proof registry.
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>

static uint8_t *decisions;
static uint64_t named_counts[3];
static uint64_t selected_expanded;
static uint32_t context_mask;
static int radius, window, max_length, mode;
static int perm[24][4], perm_count;
static char letters[24];

static void die(const char *reason) {
    fprintf(stderr, "AUDIT_ERROR: %s\n", reason);
    exit(2);
}

static int alphabet_group_member(const char *kind, const int p[4]) {
    if (strcmp(kind,"s4")==0) return 1;
    if (strcmp(kind,"s3")==0) return p[3]==3;
    if (strcmp(kind,"v4i")==0)
        return p[0]<2 && p[1]<2 && p[2]>=2 && p[3]>=2;
    if (strcmp(kind,"a4")==0) {
        int inversions=0;
        for(int i=0;i<4;i++) for(int j=i+1;j<4;j++)
            inversions += (p[i]>p[j]);
        return (inversions%2)==0;
    }
    die("unexpected subgroup type");
    return 0;
}

static void enumerate_group(const char *kind, int expected_order) {
    for(int a=0;a<4;a++) for(int b=0;b<4;b++)
    for(int c=0;c<4;c++) for(int d=0;d<4;d++) {
        if(a==b||a==c||a==d||b==c||b==d||c==d)continue;
        int p[4]={a,b,c,d};
        if(alphabet_group_member(kind,p)){
            if(perm_count==24)die("group overflow");
            for(int i=0;i<4;i++)perm[perm_count][i]=p[i];
            perm_count++;
        }
    }
    if(perm_count!=expected_order)die("wrong independent group census");
}

/* The rightmost 2*period bits describe the last period symbols. */
static int ends_in_square(uint64_t value, int length) {
    for(int period=1;period*2<=length;period++) {
        const uint64_t mask=(UINT64_C(1)<<(2*period))-1;
        if((value & mask)==((value>>(2*period))&mask))return 1;
    }
    return 0;
}

static void load_selected(const char *file, size_t expected_orbits) {
    const size_t bit_bytes=((size_t)1)<<(2*window-3);
    decisions=(uint8_t*)calloc(bit_bytes,1);
    if(!decisions)die("cannot allocate full named-word decision bitset");
    FILE *source=fopen(file,"rb");
    if(!source)die("cannot open original selected-context file");
    char line[64];
    size_t seen_orbits=0;
    while(fgets(line,sizeof(line),source)) {
        size_t length=strcspn(line,"\r\n");
        if(length!=(size_t)window)die("selected word has wrong width");
        for(size_t t=0;t<length;t++)
            if(line[t]<'0'||line[t]>'3')die("selected word outside alphabet");
        uint64_t source_word=0;
        int used=0;
        for(int t=0;t<window;t++){
            const int letter=line[t]-'0';
            used|=1<<letter;
            source_word=(source_word<<2)|(uint64_t)letter;
            if(ends_in_square(source_word,t+1))
                die("selected context is not square-free");
        }
        int kinds=0;
        for(int t=0;t<4;t++)kinds+=(used>>t)&1;
        if(kinds<3)die("invalid selected source uses fewer than 3 letters");
        for(int g=0;g<perm_count;g++) {
            uint32_t id=0;
            for(int t=0;t<window;t++)
                id=(id<<2)|(uint32_t)perm[g][line[t]-'0'];
            const uint8_t bit=(uint8_t)(1u<<(id&7));
            if(decisions[id>>3]&bit)
                die("duplicate named decision after symmetry expansion");
            decisions[id>>3]|=bit;
            selected_expanded++;
        }
        seen_orbits++;
    }
    if(ferror(source))die("read error in selected-word table");
    fclose(source);
    if(seen_orbits!=expected_orbits ||
       selected_expanded!=expected_orbits*(size_t)perm_count)
        die("selected-word orbit and named expansion counts mismatch");
}

static int marked(uint64_t full, int length, int offset) {
    if(mode==1)return 0; /* known-invalid all-zero rule */
    if(mode==2)return 1; /* known-invalid all-one rule */
    const int shift=2*(length-window-offset);
    if(shift<0)die("invalid context offset");
    const uint32_t id=(uint32_t)((full>>shift)&context_mask);
    return (decisions[id>>3]>>(id&7))&1;
}

static void counterexample(const char *problem, int n) {
    fprintf(stderr,"RULE_FAILURE %s at length=%d word=",problem,n);
    for(int i=0;i<n;i++)fputc(letters[i],stderr);
    fputc('\n',stderr);
    exit(3);
}

/* No alphabet-symmetry pruning of any source word or prefix. */
static void exhaustive(uint64_t full, int length) {
    if(length==window+1){
        named_counts[0]++;
        if(marked(full,length,0)&&marked(full,length,1))
            counterexample("distance1",length);
    }
    if(length==window+2){
        named_counts[1]++;
        if(marked(full,length,0)&&marked(full,length,2))
            counterexample("distance2",length);
    }
    if(length==max_length){
        named_counts[2]++;
        int covered=0;
        for(int i=0;i<5;i++)covered|=marked(full,length,i);
        if(!covered)counterexample("covering",length);
        return;
    }
    for(int symbol=0;symbol<4;symbol++){
        letters[length]=(char)('0'+symbol);
        uint64_t extension=(full<<2)|(uint64_t)symbol;
        if(!ends_in_square(extension,length+1))
            exhaustive(extension,length+1);
    }
}

int main(int argc,char **argv) {
    if(argc!=4)die("expected: case selected-file mode(valid|none|all)");
    const char *name=argv[1];
    if(strcmp(name,"s4")==0){radius=7;perm_count=0;}
    else if(strcmp(name,"a4")==0 || strcmp(name,"s3")==0 ||
            strcmp(name,"v4i")==0){radius=6;perm_count=0;}
    else die("unrecognized case");
    window=2*radius+1;
    max_length=window+4;
    if(strcmp(argv[3],"valid")==0)mode=0;
    else if(strcmp(argv[3],"none")==0)mode=1;
    else if(strcmp(argv[3],"all")==0)mode=2;
    else die("invalid validation mode");
    const int expected_order=(strcmp(name,"s4")==0?24:
        strcmp(name,"a4")==0?12:strcmp(name,"s3")==0?6:4);
    const size_t expected_selected=(strcmp(name,"s4")==0?47142:
        strcmp(name,"a4")==0?13611:strcmp(name,"s3")==0?27586:41760);
    enumerate_group(name,expected_order);
    context_mask=(uint32_t)((UINT64_C(1)<<(2*window))-1);
    load_selected(argv[2],expected_selected);
    exhaustive(0,0);
    const uint64_t c1=radius==7?UINT64_C(10895952):UINT64_C(1585128);
    const uint64_t c2=radius==7?UINT64_C(28566216):UINT64_C(4156392);
    const uint64_t c3=radius==7?UINT64_C(196322976):UINT64_C(28566216);
    if(named_counts[0]!=c1 || named_counts[1]!=c2 ||
       named_counts[2]!=c3)
        die("exhaustive named source census differs from independent expected count");
    printf("VERIFIED_NAMED case=%s radius=%d group_order=%d "
           "selected_orbits=%zu expanded_decisions=%" PRIu64
           " length%d=%" PRIu64 " length%d=%" PRIu64
           " length%d=%" PRIu64 "\n",
           name,radius,perm_count,expected_selected,selected_expanded,
           window+1,named_counts[0],window+2,named_counts[1],
           max_length,named_counts[2]);
    free(decisions);
    return 0;
}
