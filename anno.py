"""
annotate nucleotide position(s) or mutations
"""
import sys, argparse, re
from transcripts import *
from utils import *
from mutation import parse_tok_mutation_str, list_parse_mutation, parser_add_mutation
from record import *

def pos2codon(thash, chrm, pos):

    for t in thash.get_transcripts(chrm, pos):
        c = t.npos2codon(chrm, pos)
        yield t, c

def pos2codon_longest(thash, chrm, pos):

    longest = None
    longest_c = None
    for t, c in pos2codon(thash,chrm,pos):
        if (not longest) or len(longest) < len(t):
            longest = t
            longest_c = c

    if longest:
        yield longest, longest_c

def _main_core_(args, thash, q):

    if args.longest:
        tc_iter = pos2codon_longest(thash, q.tok, q.pos)
    else:
        tc_iter = pos2codon(thash, q.tok, q.pos)

    found = False
    for t, c in tc_iter:
        if isinstance(c, Codon):
            found = True

            r = Record()
            r.chrm = t.chrm
            r.tname = t.name
            r.reg = '%s (%s, coding)' % (t.gene.name, t.strand)
            r.pos = '-'.join(map(str, c.locs))

            # at the ends of retained intron transcripts from ENSEMBL,
            # codon sequence is not always of length 3
            if c.seq in standard_codon_table:
                r.taa_ref = standard_codon_table[c.seq]
            r.taa_pos = c.index
            if q.alt:
                if c.strand == "+":
                    alt_seq = set_seq(c.seq, c.locs.index(q.pos), q.alt)
                else:
                    alt_seq = set_seq(c.seq, 2-c.locs.index(q.pos), complement(q.alt))
                r.taa_alt = standard_codon_table[alt_seq]

            r.gnuc_pos = q.pos
            r.gnuc_ref = c.refseq()[c.locs.index(q.pos)]
            r.gnuc_alt = q.alt

            if c.strand == '+':
                r.tnuc_ref = r.gnuc_ref
                r.tnuc_alt = r.gnuc_alt
                r.tnuc_pos = (c.index-1)*3 + c.locs.index(q.pos) + 1
            else:
                r.tnuc_ref = complement(r.gnuc_ref)
                r.tnuc_alt = complement(r.gnuc_alt) if r.gnuc_alt else ''
                r.tnuc_pos = c.index*3 - c.locs.index(q.pos)

            r.format(q.op)

        elif isinstance(c, NonCoding):
            found = True

            r = Record()
            r.chrm = t.chrm
            r.gnuc_pos = q.pos
            r.tname = t.name
            r.reg = '%s (%s noncoding)' % (t.gene.name, t.strand)
            r.info = c.format()
            r.format(q.op)

    if not found:
        r = Record()
        r.gnuc_ref = q.ref
        r.gnuc_alt = q.alt
        r.gnuc_pos = q.pos
        r.info = 'status=NoValidTranscriptFound'
        r.format(q.op)


def main_list(args, thash):

    for q, line in list_parse_mutation(args):
        _main_core_(args, thash, q)

def main_one(args, thash):
    q = parse_tok_mutation_str(args.i)
    q.op = args.i
    _main_core_(args, thash, q)


def main(args):

    name2gene, thash = parse_annotation(args)

    if args.l:
        main_list(args, thash)

    if args.i:
        main_one(args, thash)

# def main(args):

#     name2gene, thash = parse_annotation(args)
#     for line in args.l:
#         fields = line.strip().split('\t')
#         name = fields[int(args.i)-1]
#         tn = fields[int(args.t)-1]
#         if name in name2gene:
#             gene = name2gene[name]
#             ts = [t for t in gene.tpts if tn == t.name]
#             if ts:
#                 o = len([t for t in gene.tpts if len(t) > len(ts[0])])
#                 print o
    
def add_parser_anno(subparsers, d):

    parser = subparsers.add_parser('anno', help=__doc__)
    parser_add_annotation(parser, d)
    parser_add_mutation(parser)
    # parser.add_argument('-i', default=None,
    #                     help="<chrm>:[<ref>]<pos>[<alt>], E.g., chr12:25398285")
    # parser.add_argument('-l', default=None,
    #                     type = argparse.FileType('r'),
    #                     help='mutation list file')
    # parser.add_argument('-d', default="\t", 
    #                     help="table delimiter of mutation list [\\t]")
    # parser.add_argument('-c', type=int, default=-1,
    #                     help='column for chromosome (1-based)')
    # parser.add_argument("-p", type=int, default=-1,
    #                     help='column for position (1-based)')
    # parser.add_argument('-r', type=int, default=-1,
    #                     help='column for reference base (1-based)')
    # parser.add_argument('-v', type=int, default=-1,
    #                     help='column for variant base (1-based)')
    # parser.add_argument('-t', type=int, default=-1,
    #                     help='columns for preferred transcript (1-based)')
    # parser.add_argument("-m", type=int, default=-1,
    #                     help="column for mutation in format <chrm>:[<ref>]<pos>[<alt>] (1-based)")
    # parser.add_argument('-o', default='-',
    #                     help='columns in the original table to be output (1-based)')
    # parser.add_argument('--skipheader', action='store_true',
    #                     help='skip header')
    parser.add_argument('--longest', action="store_true",
                        help='use longest transcript instead of reporting all transcripts')

    parser.set_defaults(func=main)
