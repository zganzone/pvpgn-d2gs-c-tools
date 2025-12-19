#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <sys/types.h>
#include <dirent.h>

// --- CORE CONSTANTS AND OFFSETS (1.14d PvPGN) ---
#define D2S_LEVEL_OFFSET 0x2B     // Character Level (1 byte)
#define D2S_CLASS_OFFSET 0x28     // Character Class (1 byte)
#define D2S_DEAD_FLAG_OFFSET 0x24 // Dead/Alive flag (1 byte, bit 3)

#define MAX_CHARNAME_LEN 16
#define MAX_ACCTNAME_LEN 16

// Item Constants 
#define ITEM_LIST_MARKER "JM"
#define ITEM_LOWQUAL	1
#define ITEM_NORMALQUAL	2
#define ITEM_HIGHQUAL	3 
#define ITEM_MAGIC	4     
#define ITEM_SET	5     
#define ITEM_RARE	6     
#define ITEM_UNIQ	7     
#define ITEM_CRAFTED	8
#define ITEM_UNIQ_SOJ	122


// --- STRUCTURES ---

typedef struct {
	int magicword; int version; int create_time; int last_time; int checksum;
	int total_play_time; int reserved[6];
	unsigned char charname[MAX_CHARNAME_LEN];   
	unsigned char account[MAX_ACCTNAME_LEN];    
	unsigned char realmname[32];
} t_d2charinfo_header;

struct filebuf { char *buf; int bufsize; };
struct d2s_item {
	int dontcare1:32; int dontcare2:5; int simple:1; int dontcare3:32; int dontcare4:6;
	int c1:8; int c2:8; int c3:8; int c4:8; int dontcare5:32; int dontcare6:10;
	int quality:4; int isring:1; int ringpic:3; int classspec:1; int uniqident:12;
} __attribute__((__packed__));
struct itemlist { struct d2s_item *item; struct itemlist *next; };

struct stats {
	int total; int lowqual; int normalqual; int highqual; int magic; int set; 
	int rare; int uniq; int crafted; int soj;
};

// --- GLOBAL CONFIGURATION (for CLI arguments) ---
typedef struct {
    char *charname;
    char *accountname;
    char *charinfo_dir;
    char *charsave_dir;
    char *output_filepath;
    int mode_all;
    int format_json;
    int format_xml;
} t_config;


// --- FUNCTION DECLARATIONS ---
struct filebuf* readfile(const char*);
struct itemlist* find_itemlist(struct filebuf*);
struct stats* parse_itemlist(struct itemlist*);
void print_stats(struct stats*);
void print_char_info(const char* charname, const char* accountname, struct filebuf* mybuf, t_config *conf);
void output_json(const char* charname, const char* accountname, struct filebuf* charsave_fb, struct filebuf* charinfo_fb, struct stats* item_stats, t_config *conf);
void parse_cli_args(int argc, char *argv[], t_config *conf);
const char* get_char_class(unsigned char class_id);
void xerrorexit(const char*, const char*);


// --- MAIN FUNCTION ---

int main(int argc, char *argv[]) {
    t_config config;
    struct filebuf *charsave_fb = NULL;
    struct filebuf *charinfo_fb = NULL;
    struct stats *s = NULL;
    char *charsave_path = NULL;
    char *charinfo_path = NULL;
    
    // Initialize config with NULL/0
    memset(&config, 0, sizeof(t_config));
    
    // 1. Parse CLI arguments
    parse_cli_args(argc, argv, &config);

    if (config.mode_all) {
        fprintf(stderr, "Error: The '-all' functionality is not yet implemented in this simplified code.\n");
        return EXIT_FAILURE;
    }
    
    if (!config.charname || !config.accountname) {
        fprintf(stderr, "Usage: %s -c <charname> -a <accountname> [OPTIONS]\n", argv[0]);
        fprintf(stderr, "Example: %s -c sorsi -a zgan -pvpdir=/usr/local/pvpgn/var/pvpgn/ -json -f /tmp/sorsi.json\n", argv[0]);
        return EXIT_FAILURE;
    }

    // Check for required directory paths
    if (!config.charsave_dir || !config.charinfo_dir) {
        fprintf(stderr, "Error: Must specify PVPGN directories using -pvpdir or -csd/-cid.\n");
        return EXIT_FAILURE;
    }

    // 2. Construct charsave path
    int path_len;
    
    path_len = strlen(config.charsave_dir) + 1 + strlen(config.charname) + 1;
    charsave_path = malloc(path_len);
    snprintf(charsave_path, path_len, "%s/%s", config.charsave_dir, config.charname);

    // 3. Read CharSave file
    charsave_fb = readfile(charsave_path);
    if (charsave_fb == NULL) { goto cleanup; }

    // 4. Construct CharInfo path (charinfo_dir/accountname/charname)
    path_len = strlen(config.charinfo_dir) + 1 + strlen(config.accountname) + 1 + strlen(config.charname) + 1;
    charinfo_path = malloc(path_len);
    snprintf(charinfo_path, path_len, "%s/%s/%s", config.charinfo_dir, config.accountname, config.charname);
    
    // 5. Read CharInfo file
    charinfo_fb = readfile(charinfo_path);

    // 6. Item Analysis
    s = parse_itemlist(find_itemlist(charsave_fb));

    // --- OUTPUT ---
    if (config.format_json) {
        output_json(config.charname, config.accountname, charsave_fb, charinfo_fb, s, &config);
    } else if (config.format_xml) {
        fprintf(stderr, "Error: XML output is not yet implemented.\n");
    } else {
        // Standard Console Output
        printf("--- CHARACTER ANALYSIS ---\n");
        print_char_info(config.charname, config.accountname, charsave_fb, &config);
        print_stats(s);
    }
    
    // --- CLEANUP ---
cleanup:
    if (charsave_path) free(charsave_path);
    if (charinfo_path) free(charinfo_path);
    if (charsave_fb) { free(charsave_fb->buf); free(charsave_fb); }
    if (charinfo_fb) { free(charinfo_fb->buf); free(charinfo_fb); }
    if (s) free(s);

    return EXIT_SUCCESS;
}


// --- CLI ARGUMENT PARSER ---
void parse_cli_args(int argc, char *argv[], t_config *conf) {
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-all") == 0) { conf->mode_all = 1; } 
        else if (strcmp(argv[i], "-json") == 0) { conf->format_json = 1; } 
        else if (strcmp(argv[i], "-o") == 0) { conf->format_json = 1; } // Alias for -json
        else if (strcmp(argv[i], "-xml") == 0) { conf->format_xml = 1; }
        else if (strcmp(argv[i], "-c") == 0 && i + 1 < argc) { conf->charname = argv[++i]; } 
        else if (strcmp(argv[i], "-a") == 0 && i + 1 < argc) { conf->accountname = argv[++i]; } 
        else if (strncmp(argv[i], "-pvpdir=", 8) == 0) { 
            conf->charinfo_dir = argv[i] + 8;
            conf->charsave_dir = argv[i] + 8;
        }
        else if (strncmp(argv[i], "-cid=", 5) == 0) { conf->charinfo_dir = argv[i] + 5; } 
        else if (strncmp(argv[i], "-csd=", 5) == 0) { conf->charsave_dir = argv[i] + 5; } 
        else if (strncmp(argv[i], "-f=", 3) == 0) { conf->output_filepath = argv[i] + 3; }
    }
}


// --- JSON OUTPUT FUNCTION ---

void output_json(const char* charname, const char* accountname, struct filebuf* charsave_fb, struct filebuf* charinfo_fb, struct stats* item_stats, t_config *conf) {
    
    FILE *output = stdout; 
    
    if (conf->output_filepath) {
        output = fopen(conf->output_filepath, "w");
        if (output == NULL) {
            fprintf(stderr, "Error: Cannot open output file %s: %s\n", conf->output_filepath, strerror(errno));
            return;
        }
    }

    t_d2charinfo_header *charinfo_h = (charinfo_fb != NULL) ? (t_d2charinfo_header*)charinfo_fb->buf : NULL;
    
    // Read basic info from charsave
    unsigned char level = *(unsigned char*)(charsave_fb->buf + D2S_LEVEL_OFFSET);
    unsigned char class_id = *(unsigned char*)(charsave_fb->buf + D2S_CLASS_OFFSET);

    fprintf(output, "{\n");
    fprintf(output, "  \"character_info\": {\n");
    
    // Print names from charinfo (with casting fix)
    fprintf(output, "    \"name\": \"%s\",\n", 
        (charinfo_h != NULL) ? (char*)charinfo_h->charname : charname);
    fprintf(output, "    \"account_name\": \"%s\",\n", 
        (charinfo_h != NULL) ? (char*)charinfo_h->account : accountname);
    
    // Print stats from charsave
    fprintf(output, "    \"level\": %d,\n", level);
    // Note: This is the LAST field in this block, so it does not end with a comma.
    fprintf(output, "    \"class\": \"%s\"\n", get_char_class(class_id)); 
    
    // The "status" field has been removed as requested.
    
    fprintf(output, "  },\n");
    fprintf(output, "  \"item_stats\": {\n");
    fprintf(output, "    \"total_items\": %d,\n", item_stats->total);
    fprintf(output, "    \"low_quality\": %d,\n", item_stats->lowqual);
    fprintf(output, "    \"normal\": %d,\n", item_stats->normalqual);
    fprintf(output, "    \"high_quality\": %d,\n", item_stats->highqual);
    fprintf(output, "    \"magic\": %d,\n", item_stats->magic);
    fprintf(output, "    \"set\": %d,\n", item_stats->set);
    fprintf(output, "    \"rare\": %d,\n", item_stats->rare);
    fprintf(output, "    \"unique\": %d,\n", item_stats->uniq);
    fprintf(output, "    \"crafted\": %d,\n", item_stats->crafted);
    fprintf(output, "    \"soj_count\": %d\n", item_stats->soj);
    fprintf(output, "  }\n");
    fprintf(output, "}\n");
    
    if (output != stdout) {
        printf("JSON output successfully written to %s\n", conf->output_filepath);
        fclose(output);
    }
}

// --- CONSOLE OUTPUT FUNCTION ---

void print_char_info(const char* charname, const char* accountname, struct filebuf* mybuf, t_config *conf) {

    int path_len = strlen(conf->charinfo_dir) + 1 + strlen(accountname) + 1 + strlen(charname) + 1;
	char* charinfo_path = malloc(path_len);
    snprintf(charinfo_path, path_len, "%s/%s/%s", conf->charinfo_dir, accountname, charname);
    
    struct filebuf* charinfo_fb = readfile(charinfo_path);
	t_d2charinfo_header *charinfo_h = NULL;
    
    unsigned char class_id = *(unsigned char*)(mybuf->buf + D2S_CLASS_OFFSET);
    unsigned char dead_flag = *(unsigned char*)(mybuf->buf + D2S_DEAD_FLAG_OFFSET);
    unsigned char level = *(unsigned char*)(mybuf->buf + D2S_LEVEL_OFFSET);

	if (charinfo_fb != NULL) {
		charinfo_h = (t_d2charinfo_header*)charinfo_fb->buf;
		printf("Character Name (CharInfo): %s\n", (char*)charinfo_h->charname);
		printf("Account Name (CharInfo): %s\n", (char*)charinfo_h->account);
		free(charinfo_fb->buf);
		free(charinfo_fb);
	} else {
		printf("Character Name: %s (CharInfo file not found)\n", charname);
		printf("Account Name: %s (CharInfo file not found)\n", accountname);
	}
	free(charinfo_path);
	
	printf("Level (CharSave): %d\n", level);
    printf("Class: %s\n", get_char_class(class_id));
    printf("Status: %s\n", (dead_flag & 0x8) ? "Dead" : "Alive");
}

void print_stats(struct stats *s) {
	printf("--- ITEM STATS ---\n");
	printf("Total Items: %4d\n", s->total);
	printf("   -> Low Quality: %4d\n", s->lowqual);
	printf("   -> Normal:      %4d\n", s->normalqual);
	printf("   -> High Quality: %4d\n", s->highqual);
	printf("   -> Magic:       %4d\n", s->magic);
	printf("   -> Set:         %4d\n", s->set);
	printf("   -> Rare:        %4d\n", s->rare);
	printf("   -> Unique:      %4d\n", s->uniq);
	printf("   -> Crafted:     %4d\n", s->crafted);
	printf("   -> SoJ:         %2d\n", s->soj);
}

const char* get_char_class(unsigned char class_id) {
    switch (class_id) {
        case 0: return "Amazon";
        case 1: return "Sorceress";
        case 2: return "Necromancer";
        case 3: return "Paladin";
        case 4: return "Barbarian";
        case 5: return "Druid";
        case 6: return "Assassin";
        default: return "Unknown";
    }
}

// --- UTILITY FUNCTIONS (readfile, find_itemlist, parse_itemlist, xerrorexit) ---

struct filebuf* readfile(const char *filename) {
    FILE *file; char *buf; long bufsize;
    file = fopen(filename, "rb"); if (file == NULL) { fprintf(stderr, "readfile() Error: Cannot open file '%s': %s\n", filename, strerror(errno)); return NULL; }
    fseek(file, 0, SEEK_END); bufsize = ftell(file); fseek(file, 0, SEEK_SET);
    if (bufsize == 0) { fprintf(stderr, "readfile() Error: File '%s' is empty.\n", filename); fclose(file); return NULL; }
    buf = malloc(bufsize); if (buf == NULL) { xerrorexit("Memory allocation error", "readfile()"); }
    if (fread(buf, 1, bufsize, file) != bufsize) { fprintf(stderr, "readfile() Error: Error reading file '%s'.\n", filename); free(buf); fclose(file); return NULL; }
    fclose(file);
    struct filebuf *mybuf = malloc(sizeof(struct filebuf));
    if (mybuf == NULL) { xerrorexit("Memory allocation error", "readfile()"); }
    mybuf->buf = buf; mybuf->bufsize = (int)bufsize; return mybuf;
}

struct itemlist* find_itemlist(struct filebuf* mybuf)
{
    char *buf = mybuf->buf; int i, gotfirst=0; struct itemlist *ptr = malloc(sizeof(struct itemlist)); struct itemlist *retval = ptr;
    if(!ptr) { xerrorexit("Memory allocation error", "find_itemlist()"); }
    ptr->next = NULL; ptr->item = NULL;
    for(i=0; i < mybuf->bufsize; i++) {
        if(i+1 < mybuf->bufsize)
        if(buf[i] == ITEM_LIST_MARKER[0] && buf[i+1] == ITEM_LIST_MARKER[1]) {
            if(gotfirst == 0) { gotfirst = 1; continue; }
            if(i+3 < mybuf->bufsize && buf[i+2] == 0 && buf[i+3] == 0) { break; }
            ptr->item = (struct d2s_item*)(buf + i);
            if(ptr->item->simple) { ptr->item = NULL; continue; }
            ptr->next = malloc(sizeof(struct itemlist));
            if(!(ptr->next)) xerrorexit("Memory allocation error", "find_itemlist()");
            ptr->next->next = NULL; ptr = ptr->next;
        }
    }
    return retval;
}

struct stats* parse_itemlist(struct itemlist* items)
{
    struct stats *ret = malloc(sizeof(struct stats)); struct itemlist *ptr = items;
    memset(ret, 0, sizeof(struct stats));
    while(ptr != NULL && ptr->item != NULL) {
        ret->total++;
        switch(ptr->item->quality) {
            case ITEM_LOWQUAL: ret->lowqual++; break;
            case ITEM_NORMALQUAL: ret->normalqual++; break;
            case ITEM_HIGHQUAL: ret->highqual++; break;
            case ITEM_MAGIC: ret->magic++; break;
            case ITEM_SET: ret->set++; break;
            case ITEM_RARE: ret->rare++; break;
            case ITEM_UNIQ: ret->uniq++; break;
            case ITEM_CRAFTED: ret->crafted++; break;
        }
        if(ptr->item->quality == ITEM_UNIQ && ptr->item->isring && !ptr->item->classspec && ptr->item->uniqident == ITEM_UNIQ_SOJ) {
            ret->soj++;
        }
        ptr = ptr->next;
    }
    return ret;
}

void xerrorexit(const char *message, const char *cause)
{
	fprintf(stderr, "%s: %s\n", cause, message);
	exit(EXIT_FAILURE);
}
