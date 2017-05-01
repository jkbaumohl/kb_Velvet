/*
A KBase module: Velvet

This is a KBase module that wraps the open source package "Short read de novo assembler using de Bruijn graphs"
Version 1.2.10

References:
https://github.com/dzerbino/velvet
https://github.com/dzerbino/velvet/blob/master/Columbus_manual.pdf
*/

module Velvet {
    /* 
        A 'typedef' allows you to provide a more specific name for
        a type.  Built-in primitive types include 'string', 'int',
        'float'.  Here we define a type named assembly_ref to indicate
        a string that should be set to a KBase ID reference to an
        Assembly data object.
    */

    /* A boolean. 0 = false, anything else = true. */
    typedef int bool;

    /* Arguments for run_velveth
velveth, help

Compilation settings:
CATEGORIES = 2
MAXKMERLENGTH = 31

Usage:
./velveth out_folder hash_length {[-file_format][-read_type][-separate|-interleaved] filename1 [filename2 ...]} {...} [options]

        out_folder       : directory name for output files
        hash_length     : EITHER an odd integer (if even, it will be decremented) <= 31 (if above, will be reduced)
                        : OR: m,M,s where m and M are odd integers (if not, they will be decremented) with m < M <= 31 (if above, will be reduced)
                                and s is a step (even number). Velvet will then hash from k=m to k=M with a step of s
        file_name        : path to sequence file or - for standard input

File format options:
        -fasta  -fastq  -raw    -fasta.gz       -fastq.gz       -raw.gz -sam    -bam    -fmtAuto
        (Note: -fmtAuto will detect fasta or fastq, and will try the following programs for decompression : gunzip, pbunzip2, bunzip2

File layout options for paired reads (only for fasta and fastq formats):
        -interleaved    : File contains paired reads interleaved in the one file (default)
        -separate       : Read 2 separate files for paired reads

Read type options:
        -short  -shortPaired
        -short2 -shortPaired2
        -long   -longPaired
        -reference

Options:
        -strand_specific        : for strand specific transcriptome sequencing data (default: off)
        -reuse_Sequences        : reuse Sequences file (or link) already in directory (no need to provide original filenames in this case (default: off)
        -reuse_binary   : reuse binary sequences file (or link) already in directory (no need to provide original filenames in this case (default: off)
        -noHash                 : simply prepare Sequences file, do not hash reads or prepare Roadmaps file (default: off)
        -create_binary          : create binary CnyUnifiedSeq file (default: off)

Synopsis:

- Short single end reads:
        velveth Assem 29 -short -fastq s_1_sequence.txt

- Paired-end short reads (remember to interleave paired reads):
        velveth Assem 31 -shortPaired -fasta interleaved.fna

- Paired-end short reads (using separate files for the paired reads)
        velveth Assem 31 -shortPaired -fasta -separate left.fa right.fa

- Two channels and some long reads:
        velveth Assem 43 -short -fastq unmapped.fna -longPaired -fasta SangerReads.fasta

- Three channels:
        velveth Assem 35 -shortPaired -fasta pe_lib1.fasta -shortPaired2 pe_lib2.fasta -short3 se_lib1.fa

Output:
        out_folder/Roadmaps
        out_folder/Sequences
                [Both files are picked up by graph, so please leave them there]

    Here is the test examples and their stdout printouts:
root@c50eaaa56231:/kb/module# ls /data
__READY__  velvet_data
root@c50eaaa56231:/kb/module# cd /velvet_data/
root@c50eaaa56231:/velvet_data# ls
test_long.fa  test_reads.fa  test_reads.sam  test_reference.fa
root@c50eaaa56231:/velvet_data# sort test_reads.sam > mySortedReads.sam
root@c50eaaa56231:/velvet_data# velveth test_dir 21 -reference test_reference.fa -shortPaired -sam mySortedReads.sam
[0.000000] Reading FastA file test_reference.fa;
[0.006270] 1 sequences found
[0.006299] Done
[0.006331] Reading SAM file mySortedReads.sam
[0.246146] 142858 reads found.
[0.246170] Done
[0.246172] Reference mapping counters
[0.246173] Name Read mappings
[0.246174] SEQUENCE     142858
[0.246222] Reading read set file test_dir/Sequences;
[0.259455] 142859 sequences found
[0.259559] Read 1 of length 32773, longer than limit 32767
[0.259575] You should modify recompile with the LONGSEQUENCES option (cf. manual)
        string workspace_name - the name of the workspace for input/output
        string out_folder; #folder name for output files
        int hash_length; #EITHER an odd integer (if even, it will be decremented) <= 31 (if above, will be reduced)L
        string filename; #path to sequence file or - for standard input
        string file_format; #e.g., -fasta, -fastq, -raw,-fasta.gz, -fastq.gz, -raw.gz, -sam, -bam, -fmtAuto
        string file_layout; #e.g., -interleaved or -separate 
        string read_type; #e.g., -short, -shortPaired, short2, shortPaired2, -long, -longPaired, or -reference
    */
    /*
        Define a structure that holds the read file name and its use.
        Note: only read_file_name is required, the rest are optional.
        e.g., {"reference_file" => "test_reference.fa", "read_file_name" => "mySortedReads.sam", "left_file" => "left.fa", "right_file" => "right.fa"}
    */ 
    typedef structure { 
        string read_file;
        string reference_file;
        string left_file;
        string right_file;
    } ReadFileInfo;


    typedef structure {
        string read_type; 
        string file_format; 
        ReadFileInfo read_file_info;
        string file_layout; 
    } ReadsChannel;

    typedef structure {
        string out_folder; 
        string workspace_name;
        int hash_length; 
        list<ReadsChannel> reads_channels; 
    } VelvethParams;
    
    /* Output parameter(s) for run_velveth and run_velvetg

    report_name - the name of the KBaseReport.Report workspace object.
    report_ref - the workspace reference of the report.

    */
    typedef structure {
        string report_name;
        string report_ref;
    } VelvetResults;
    
    /* Definition of run_velveth
     */
    funcdef run_velveth(VelvethParams params) returns (VelvetResults output) authentication required;


    /* Arguments for run_velvetg
        wk_folder                       : working directory name

Standard options:
        -cov_cutoff <floating-point|auto>       : removal of low coverage nodes AFTER tour bus or allow the system to infer it
                (default: no removal)
        -ins_length <integer>           : expected distance between two paired end reads (default: no read pairing)
        -read_trkg <yes|no>             : tracking of short read positions in assembly (default: no tracking)
        -min_contig_lgth <integer>      : minimum contig length exported to contigs.fa file (default: hash length * 2)
        -amos_file <yes|no>             : export assembly to AMOS file (default: no export)
        -exp_cov <floating point|auto>  : expected coverage of unique regions or allow the system to infer it
                (default: no long or paired-end read resolution)
        -long_cov_cutoff <floating-point>: removal of nodes with low long-read coverage AFTER tour bus
                (default: no removal)

Advanced options:
        -ins_length* <integer>          : expected distance between two paired-end reads in the respective short-read dataset (default: no read pairing)
        -ins_length_long <integer>      : expected distance between two long paired-end reads (default: no read pairing)
        -ins_length*_sd <integer>       : est. standard deviation of respective dataset (default: 10% of corresponding length)
                [replace '*' by nothing, '2' or '_long' as necessary]
        -scaffolding <yes|no>           : scaffolding of contigs used paired end information (default: on)
        -max_branch_length <integer>    : maximum length in base pair of bubble (default: 100)
        -max_divergence <floating-point>: maximum divergence rate between two branches in a bubble (default: 0.2)
        -max_gap_count <integer>        : maximum number of gaps allowed in the alignment of the two branches of a bubble (default: 3)
        -min_pair_count <integer>       : minimum number of paired end connections to justify the scaffolding of two long contigs (default: 5)
        -max_coverage <floating point>  : removal of high coverage nodes AFTER tour bus (default: no removal)
        -coverage_mask <int>    : minimum coverage required for confident regions of contigs (default: 1)
        -long_mult_cutoff <int>         : minimum number of long reads required to merge contigs (default: 2)
        -unused_reads <yes|no>          : export unused reads in UnusedReads.fa file (default: no)
        -alignments <yes|no>            : export a summary of contig alignment to the reference sequences (default: no)
        -exportFiltered <yes|no>        : export the long nodes which were eliminated by the coverage filters (default: no)
        -clean <yes|no>                 : remove all the intermediary files which are useless for recalculation (default : no)
        -very_clean <yes|no>            : remove all the intermediary files (no recalculation possible) (default: no)
        -paired_exp_fraction <float>   : remove all the paired end connections which less than the specified fraction of the expected count (default: 0.1)
        -shortMatePaired* <yes|no>      : for mate-pair libraries, indicate that the library might be contaminated with paired-end reads (default no)
        -conserveLong <yes|no>          : preserve sequences with long reads in them (default no)

Output:
        wk_folder/contigs.fa            : fasta file of contigs longer than twice hash length
        wk_folder/stats.txt             : stats file (tab-spaced) useful for determining appropriate coverage cutoff
        wk_folder/LastGraph             : special formatted file with all the information on the final graph
        wk_folder/velvet_asm.afg        : (if requested) AMOS compatible assembly file
    
Example: 
        ./velvetg wk_folder [options]
        string wk_folder; #folder name for files to work on and to save results
        float cov_cutoff; #removal of low coverage nodes AFTER tour bus or allow the system to infer it (default: no removal)
        int ins_length; #expected distance between two paired end reads (default: no read pairing)
        int read_trkg; # (1=yes|0=no) tracking of short read positions in assembly (default:0)
        int min_contig_length; #minimum contig length exported to contigs.fa file (default: hash length * 2)
        int amos_file; # (1=yes|0=no) #export assembly to AMOS file (default: 0)
        float exp_cov; # <floating point|auto>, expected coverage of unique regions or allow the system to infer it (default: no long or paired-end read resolution)
        float long_cov_cutoff; #removal of nodes with low long-read coverage AFTER tour bus(default: no removal)
     */

    typedef structure {
        string workspace_name;
        string wk_folder; 
        float cov_cutoff; 
        int ins_length; 
        int read_trkg; 
        int min_contig_length; 
        int amos_file; 
        float exp_cov; 
        float long_cov_cutoff; 
    } VelvetgParams;
   
    /* Definition of run_velvetg
     */
    funcdef run_velvetg(VelvetgParams params) returns (VelvetResults output) authentication required;
};
