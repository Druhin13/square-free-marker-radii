#!/usr/bin/env python3
"""Independently audit generalized-separator candidates for violated clauses.

Does not import witness search, SAT solver or original CNF generator.
Checks every mapping, source clause, finite square-freeness, Hall-Thue
tail memberships and D-1 separator margins. Confirms no violation is
omitted or duplicated between candidates and unresolved records.

A passing audit proves *candidate-covered* constraints arise from
bi-infinite inputs, conditional on the classical Hall-Thue theorem.
It does not imply the resulting subformula is UNSAT.

Optional additional audit requiring two separately supplied experiment manifests
(not part of this evidence distribution):
    cd evidence
    python3 -B -m scripts.audit_m3_r4_violation_extensions_independent \
      --source /path/to/violations.json \
      --candidates /path/to/candidate-certificates.json

For all supplied, published radius-four proof obligations, use the
supported driver instead: python3 -B reproduce.py --case main --report ../main.json.
"""
import argparse
from collections import Counter
from hashlib import sha256
from itertools import permutations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Additional optional experiment manifests are caller-supplied, never implicit.
EASY_SHA = "925d9b7e28384bca92f29818b97a24d37b8aabe19b39d65041c4b7ca7ca5a833"
CORE_SHA = "a2f66feec531e8cd08abe79f9a619eb0177129c482577521d735b133060467f3"
MODEL_SHA = "04b91c5095429e9896037c7ccb05b818dc6d463bd3819521ffc82a99c9fba4d7"


def require(ok,reason):
    if not ok:
        raise ValueError(reason)


def squarefree(w):
    for begin in range(len(w)):
        for length in range(1,(len(w)-begin)//2+1):
            if all(w[begin+j]==w[begin+j+length] for j in range(length)):
                return False
    return True


def contexts9():
    words=[()]
    for _ in range(9):
        new=[]
        for prefix in words:
            for symbol in range(4):
                child=prefix+(symbol,)
                if squarefree(child):
                    new.append(child)
        words=new
    require(len(words)==12768,"Unexpected context enumeration")
    return {word:i+1 for i,word in enumerate(words)}


def hall_catalog():
    phi=("012","02","1")
    t="0"
    while len(t)<16000:
        t="".join(phi[int(a)] for a in t)
    t=t[:16000]
    perms=list(permutations(range(3)))
    result={0:{""}}
    for length in range(1,14):
        members=set()
        for i in range(len(t)-length+1):
            sub=t[i:i+length]
            for p in perms:
                v="".join(str(p[int(c)]) for c in sub)
                members.add(v)
                members.add(v[::-1])
        result[length]=members
    return result


def read_word(value,length=None):
    require(isinstance(value,str) and value and not set(value)-set("0123"),
            f"Malformed word {value}")
    if length is not None:
        require(len(value)==length,"Unexpected word length")
    return value


def clause_for_source(word,role,index):
    w=tuple(map(int,word))
    marks=[index[w[i:i+9]] for i in range(len(w)-8)]
    if role=="domination":
        result=tuple(sorted(set(marks)))
        require(len(result)==5,"Unexpected duplicate positive literal")
        return {result}
    if role=="packing":
        require(len(marks)==3,"Expected three position decisions")
        return {
            tuple(sorted((-marks[i],-marks[j])))
            for i,j in ((0,1),(0,2),(1,2))
        }
    raise ValueError(f"Unknown role {role}")


def check_record(record,index,hall):
    clause=tuple(sorted(record["clause"]))
    role=record["role"]
    word=read_word(record["word"],11 if role=="packing" else 13)
    require(squarefree(word),"Source factor is not square-free")
    require(clause in clause_for_source(word,role,index),
            "Clause does not arise from source factor")

    pairs=record["mapping"]
    require(isinstance(pairs,list) and all(
        isinstance(pair,list) and len(pair)==2 and
        isinstance(pair[0],int) and isinstance(pair[1],int)
        for pair in pairs
    ),"Invalid mapping representation")
    mapping=dict(pairs)
    require(len(mapping)==len(pairs),"Repeated mapping input symbol")
    require(set(mapping)==set(map(int,word)),"Mapping domain incomplete")
    require(set(mapping.values()) == set(range(len(mapping))),
            "Mapping not a bijection onto the normalized alphabet")
    normalized="".join(str(mapping[int(c)]) for c in word)
    require(record["normalized_word"]==normalized,"Normalization mismatch")

    finite=read_word(record["finite_witness"])
    offset=record["offset"]
    require(type(offset)==int and 0<=offset<=len(finite)-len(word),
            "Invalid finite-factor embedding offset")
    require(finite[offset:offset+len(word)]==normalized,
            "Source factor does not appear in finite witness")
    require(squarefree(finite),"Finite witness contains a square")

    kind=record["kind"]
    sep=record["separator"]
    if kind=="hall":
        require(len(set(word))==3 and sep is None,
                "Invalid Hall-only witness")
        require(finite in hall[len(finite)],
                "Finite witness is not a Hall-Thue orbit factor")
    elif kind=="single-separator" or kind=="multi-separator":
        require(len(set(word))==4 and type(sep)==int and
                sep in mapping and mapping[sep]==3,
                "Invalid special-symbol mapping")
        positions=[i for i,c in enumerate(finite) if c=="3"]
        expected=1 if kind=="single-separator" else None
        if expected is not None:
            require(len(positions)==expected,"Singleton has wrong occurrence count")
        else:
            require(len(positions)>=2,"Multi-separator must occur >=2 times")
        require(len(positions)==word.count(str(sep)),
                "Extra separator introduced outside source factor")
        left=finite[:positions[0]]
        right=finite[positions[-1]+1:]
        require(left in hall[len(left)] and right in hall[len(right)],
                "Exterior tails are not Hall-Thue factors")
        if kind=="multi-separator":
            spread=positions[-1]-positions[0]
            require(positions[0]>=spread-1 and
                    len(finite)-positions[-1]-1>=spread-1,
                    "Insufficient D-1 safety margins")
    elif kind=="external-double-separator":
        require(len(set(word))==3 and sep is None,
                "External two-separator is only for ternary factors")
        positions=[i for i,c in enumerate(finite) if c=="3"]
        require(len(positions)==2,"External construction must have two separators")
        spread=positions[-1]-positions[0]
        left,right=finite[:positions[0]],finite[positions[-1]+1:]
        require(left in hall[len(left)] and right in hall[len(right)],
                "External two-separator tails not Hall-Thue factors")
        require(positions[0]>=spread-1 and
                len(finite)-positions[-1]-1>=spread-1,
                "Insufficient exterior safety margins")
    else:
        raise ValueError(f"Unknown construction type {kind}")
    return (clause,role,word)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True,
                        help="Existing radius-four violation manifest (optional external data)")
    parser.add_argument("--candidates", type=Path, required=True,
                        help="Existing candidate certificate manifest (optional external data)")
    args = parser.parse_args()
    if any(not path.is_file() or path.is_symlink()
           for path in (args.source, args.candidates)):
        parser.error("Both input manifests must exist as regular, non-symlink files")
    source_path = args.source.resolve(strict=True)
    candidates_path = args.candidates.resolve(strict=True)
    raw=source_path.read_bytes()
    source=json.loads(raw.decode("utf-8"))
    require(source.get("source_easy_cnf_sha256")==EASY_SHA and
            source.get("source_core_cnf_sha256")==CORE_SHA and
            source.get("sat_model_sha256")==MODEL_SHA,
            "Source violation manifest references wrong SAT instance")
    records=source.get("violations")
    require(isinstance(records,list) and len(records)==1377,
            "Unexpected input violations")
    source_clauses={}
    for item in records:
        c=tuple(sorted(item["clause"]))
        require(c not in source_clauses,"Repeated source violation")
        source_clauses[c]=(item["role"],item["source_factor"])
    require(Counter(v[0] for v in source_clauses.values()) ==
            {"packing":1048,"domination":329},
            "Violation category counts differ")

    data=json.loads(candidates_path.read_text(encoding="utf-8"))
    require(data.get("source_violations_sha256")==sha256(raw).hexdigest() and
            data.get("sat_model_sha256")==MODEL_SHA and
            data.get("source_core_sha256")==CORE_SHA,
            "Candidate manifest references different source")
    candidates=data.get("candidate_certificates")
    unresolved=data.get("unresolved")
    require(isinstance(candidates,list) and isinstance(unresolved,list),
            "Invalid candidates/unresolved representation")
    require(len(candidates)+len(unresolved)==len(source_clauses),
            "Candidate partition has incorrect total")

    index=contexts9()
    hall=hall_catalog()
    checked=set()
    types=Counter()
    roles=Counter()
    for item in candidates:
        clause,role,word=check_record(item,index,hall)
        require(clause in source_clauses and
                source_clauses[clause]==(role,word) and
                clause not in checked,
                "Candidate doesn't match original violation")
        checked.add(clause)
        types[item["kind"]]+=1
        roles[role]+=1
    for item in unresolved:
        c=tuple(sorted(item["clause"]))
        require(c in source_clauses and
                source_clauses[c]==(item["role"],item["source_factor"]) and
                c not in checked,
                "Invalid/duplicate unresolved record")
        checked.add(c)
    require(checked==set(source_clauses),"Some original violations were not classified")

    print("INDEPENDENT GENERALIZED-SEPARATOR CANDIDATE AUDIT PASSED")
    print("Source SAT witness SHA256:",MODEL_SHA)
    print("Source violation manifest SHA256:",sha256(raw).hexdigest())
    print("Certificate manifest SHA256:",sha256(candidates_path.read_bytes()).hexdigest())
    print("Total source violations:",len(source_clauses))
    print("Independently audited extension certificates:",len(candidates))
    print("Audited packing clauses:",roles["packing"])
    print("Audited domination clauses:",roles["domination"])
    print("Construction types:",dict(sorted(types.items())))
    print("Unresolved clauses:",len(unresolved))
    print("Classical Hall-Thue infinite-extension theorem assumed")
    print("NO r>=5 claim; no additional UNSAT certificate")


if __name__=="__main__":
    main()
