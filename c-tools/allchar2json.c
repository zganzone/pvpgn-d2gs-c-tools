#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <dirent.h>

// --- USER-DEFINED PVPGN DIRECTORIES ---
#define FIXED_CHARINFO_DIR "/usr/local/pvpgn/var/pvpgn/charinfo"
#define FIXED_CHARSAVE_DIR "/usr/local/pvpgn/var/pvpgn/charsave"
#define MAX_PATH_INPUT 1024 


// --- CORE CONSTANTS AND OFFSETS ---
#define D2S_LEVEL_OFFSET 0x2B     
#define D2S_CLASS_OFFSET 0x28     
#define D2S_DEAD_FLAG_OFFSET 0x24 
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


// --- STRUCTURES (КОРЕКЦИЯ: struct stats е преместена напред) ---

// 1. Item Stats Structure (Must be first)
struct stats {
	int total; int lowqual; int normalqual; int highqual; int magic; int set; 
	int rare; int uniq; int crafted; int soj;
};

// 2. Summary Structure (Now recognizes struct stats)
typedef struct char_summary {
    char name[MAX_CHARNAME_LEN + 1];
    char account[MAX_ACCTNAME_LEN + 1];
    int level;
    int class_id;
    struct stats item_stats;
} t_char_summary;

// 3. Global List Structure
typedef struct all_data {
    t_char_summary *list;
    int count;
    int capacity;
} t_all_data;


// 4. Other Standard Structures
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


// --- GLOBAL CONFIGURATION ---
typedef struct {
    char *charinfo_dir;
    char *charsave_dir;
    char *output_filepath;
    char input_path_buffer[MAX_PATH_INPUT]; 
    t_all_data all_chars;
} t_config;


// --- FUNCTION DECLARATIONS ---
struct filebuf* readfile(const char*);
struct itemlist* find_itemlist(struct filebuf*);
struct stats* parse_itemlist(struct itemlist*);
void output_json(const char* charname, const char* accountname, struct filebuf* charsave_fb, struct filebuf* charinfo_fb, struct stats* item_stats, t_config *conf);
void output_all_json(t_config *conf);
const char* get_char_class(unsigned char class_id);
int process_single_character(const char* charname, const char* accountname, t_config *conf);
void process_all_characters(t_config *conf);
void parse_cli_args(int argc, char *argv[], t_config *conf);
void xerrorexit(const char*, const char*);
void add_char_to_list(t_config *conf, const char *name, const char *account, int level, int class_id, struct stats *stats);


// --- MAIN FUNCTION ---

int main(int argc, char *argv[]) {
    t_config config;
    
    // 1. Инициализация
    memset(&config, 0, sizeof(t_config));
    config.charinfo_dir = FIXED_CHARINFO_DIR;
    config.charsave_dir = FIXED_CHARSAVE_DIR;
    config.all_chars.list = NULL;
    config.all_chars.count = 0;
    config.all_chars.capacity = 0;
    
    // 2. Интерактивен/CLI режим
    if (argc < 3 || strcmp(argv[1], "-o") != 0) {
        
        printf("\n--- INTERACTIVE MODE ---\n");
        printf("Please enter the output directory path for JSON files (e.g., /var/www/html/d2stats): ");
        
        if (fgets(config.input_path_buffer, MAX_PATH_INPUT, stdin) == NULL) {
            fprintf(stderr, "Error: Failed to read path input.\n");
            return EXIT_FAILURE;
        }
        
        size_t len = strlen(config.input_path_buffer);
        if (len > 0 && config.input_path_buffer[len-1] == '\n') {
            config.input_path_buffer[len-1] = '\0';
        }

        config.output_filepath = config.input_path_buffer;
        
        struct stat st; 
        if (stat(config.output_filepath, &st) == -1) {
             fprintf(stderr, "Warning: Directory '%s' does not exist. Check permissions.\n", config.output_filepath);
        }
        
        printf("--- Starting processing... ---\n");
        
    } else {
        // CLI аргумент: -o <path>
        config.output_filepath = argv[2];
    }
    

    // 3. Изпълнение на ALL MODE
    process_all_characters(&config);
    
    // 4. Final Output of the aggregated JSON file
    output_all_json(&config);

    // 5. Cleanup the list of characters
    if (config.all_chars.list) {
        free(config.all_chars.list);
    }

    return EXIT_SUCCESS;
}


// --- PROCESS ALL CHARACTERS ---

void process_all_characters(t_config *conf) {
    DIR *acct_dir = NULL;
    struct dirent *acct_list;
    
    printf("Starting ALL MODE analysis in: %s (Output to: %s)\n", conf->charinfo_dir, conf->output_filepath);

    if ((acct_dir = opendir(conf->charinfo_dir)) == NULL) {
        xerrorexit("Error opening base charinfo directory", conf->charinfo_dir);
    }

    while((acct_list = readdir(acct_dir)) != NULL) {
        if(strcmp(acct_list->d_name, ".") == 0 || strcmp(acct_list->d_name, "..") == 0) {
            continue;
        }

        char *accountname = acct_list->d_name;

        int acct_path_len = strlen(conf->charinfo_dir) + 1 + strlen(accountname) + 1;
        char *account_path = malloc(acct_path_len);
        snprintf(account_path, acct_path_len, "%s/%s", conf->charinfo_dir, accountname);

        DIR *char_dir = NULL;
        struct dirent *char_list;
        if ((char_dir = opendir(account_path)) == NULL) {
            fprintf(stderr, "Warning: Could not open account directory %s. Skipping.\n", account_path);
            free(account_path);
            continue;
        }
        
        while((char_list = readdir(char_dir)) != NULL) {
            if(strcmp(char_list->d_name, ".") == 0 || strcmp(char_list->d_name, "..") == 0) {
                continue;
            }
            
            char *charname = char_list->d_name;

            process_single_character(charname, accountname, conf);
        }

        closedir(char_dir);
        free(account_path);
    }

    closedir(acct_dir);
}


// --- PROCESS SINGLE CHARACTER ---

int process_single_character(const char* charname, const char* accountname, t_config *conf) {
    struct filebuf *charsave_fb = NULL;
    struct filebuf *charinfo_fb = NULL;
    struct stats s;
    char *charsave_path = NULL;
    char *charinfo_path = NULL;
    
    int path_len;
    
    // 1. Construct charsave path
    path_len = strlen(conf->charsave_dir) + 1 + strlen(charname) + 1;
    charsave_path = malloc(path_len);
    snprintf(charsave_path, path_len, "%s/%s", conf->charsave_dir, charname);

    // 2. Read CharSave file
    charsave_fb = readfile(charsave_path);
    if (charsave_fb == NULL) { 
        fprintf(stderr, "Warning: CharSave file not found at %s. Skipping character.\n", charsave_path);
        goto cleanup; 
    }

    // 3. Construct CharInfo path (charinfo_dir/accountname/charname)
    path_len = strlen(conf->charinfo_dir) + 1 + strlen(accountname) + 1 + strlen(charname) + 1;
    charinfo_path = malloc(path_len);
    snprintf(charinfo_path, path_len, "%s/%s/%s", conf->charinfo_dir, accountname, charname);
    
    // 4. Read CharInfo file
    charinfo_fb = readfile(charinfo_path);

    // 5. Item Analysis
    s = *parse_itemlist(find_itemlist(charsave_fb)); 
    
    // --- DATA COLLECTION ---
    unsigned char level = *(unsigned char*)(charsave_fb->buf + D2S_LEVEL_OFFSET);
    unsigned char class_id = *(unsigned char*)(charsave_fb->buf + D2S_CLASS_OFFSET);

    char temp_charname[MAX_CHARNAME_LEN + 1];
    char temp_accountname[MAX_ACCTNAME_LEN + 1];

    if (charinfo_fb != NULL) {
        t_d2charinfo_header *charinfo_h = (t_d2charinfo_header*)charinfo_fb->buf;
        strncpy(temp_charname, (char*)charinfo_h->charname, MAX_CHARNAME_LEN);
        strncpy(temp_accountname, (char*)charinfo_h->account, MAX_ACCTNAME_LEN);
    } else {
        strncpy(temp_charname, charname, MAX_CHARNAME_LEN);
        strncpy(temp_accountname, accountname, MAX_ACCTNAME_LEN);
    }
    temp_charname[MAX_CHARNAME_LEN] = '\0';
    temp_accountname[MAX_ACCTNAME_LEN] = '\0';
    
    // 6. Add to the ALL_CHAR list
    add_char_to_list(conf, temp_charname, temp_accountname, level, class_id, &s);
    
    // 7. Output Individual JSON File
    char *final_output_path = NULL;
    int final_path_len = strlen(conf->output_filepath) + 1 + strlen(charname) + 6;
    final_output_path = malloc(final_path_len);
    snprintf(final_output_path, final_path_len, "%s/%s.json", conf->output_filepath, charname);

    t_config temp_config = *conf;
    temp_config.output_filepath = final_output_path;

    output_json(charname, accountname, charsave_fb, charinfo_fb, &s, &temp_config);
    free(final_output_path);

    // --- CLEANUP ---
cleanup:
    if (charsave_path) free(charsave_path);
    if (charinfo_path) free(charinfo_path);
    if (charsave_fb) { free(charsave_fb->buf); free(charsave_fb); }
    if (charinfo_fb) { free(charinfo_fb->buf); free(charinfo_fb); }

    return EXIT_SUCCESS;
}

// --- DYNAMIC ARRAY MANAGEMENT ---

void add_char_to_list(t_config *conf, const char *name, const char *account, int level, int class_id, struct stats *stats) {
    // Resize array if necessary
    if (conf->all_chars.count >= conf->all_chars.capacity) {
        int new_capacity = conf->all_chars.capacity == 0 ? 5 : conf->all_chars.capacity * 2;
        conf->all_chars.list = (t_char_summary *)realloc(conf->all_chars.list, new_capacity * sizeof(t_char_summary));
        if (conf->all_chars.list == NULL) {
            xerrorexit("Memory allocation error", "add_char_to_list (realloc)");
        }
        conf->all_chars.capacity = new_capacity;
    }

    // Add new character summary
    t_char_summary *new_char = &conf->all_chars.list[conf->all_chars.count];
    strncpy(new_char->name, name, MAX_CHARNAME_LEN);
    strncpy(new_char->account, account, MAX_ACCTNAME_LEN);
    new_char->level = level;
    new_char->class_id = class_id;
    new_char->item_stats = *stats; // Copy the stats structure
    
    conf->all_chars.count++;
}


// --- OUTPUT ALL CHARACTERS IN ONE JSON ARRAY ---

void output_all_json(t_config *conf) {
    FILE *output = NULL;
    char *final_output_path = NULL;
    
    // 1. Construct the final filename: <base_path>/all_char_all_acc.json
    int final_path_len = strlen(conf->output_filepath) + 1 + strlen("all_char_all_acc.json") + 1;
    final_output_path = malloc(final_path_len);
    snprintf(final_output_path, final_path_len, "%s/all_char_all_acc.json", conf->output_filepath);
    
    output = fopen(final_output_path, "w");
    if (output == NULL) {
        fprintf(stderr, "Error: Cannot open final output file %s: %s\n", final_output_path, strerror(errno));
        free(final_output_path);
        return;
    }
    
    printf("Generating aggregated JSON file: %s\n", final_output_path);

    // 2. Start JSON array
    fprintf(output, "[\n");

    // 3. Loop through all collected character summaries
    for (int i = 0; i < conf->all_chars.count; i++) {
        t_char_summary *c = &conf->all_chars.list[i];

        fprintf(output, "  {\n");
        fprintf(output, "    \"character_info\": {\n");
        fprintf(output, "      \"name\": \"%s\",\n", c->name);
        fprintf(output, "      \"account_name\": \"%s\",\n", c->account);
        fprintf(output, "      \"level\": %d,\n", c->level);
        fprintf(output, "      \"class\": \"%s\"\n", get_char_class(c->class_id)); 
        fprintf(output, "    },\n");
        fprintf(output, "    \"item_stats\": {\n");
        fprintf(output, "      \"total_items\": %d,\n", c->item_stats.total);
        fprintf(output, "      \"low_quality\": %d,\n", c->item_stats.lowqual);
        fprintf(output, "      \"normal\": %d,\n", c->item_stats.normalqual);
        fprintf(output, "      \"high_quality\": %d,\n", c->item_stats.highqual);
        fprintf(output, "      \"magic\": %d,\n", c->item_stats.magic);
        fprintf(output, "      \"set\": %d,\n", c->item_stats.set);
        fprintf(output, "      \"rare\": %d,\n", c->item_stats.rare);
        fprintf(output, "      \"unique\": %d,\n", c->item_stats.uniq);
        fprintf(output, "      \"crafted\": %d,\n", c->item_stats.crafted);
        fprintf(output, "      \"soj_count\": %d\n", c->item_stats.soj);
        fprintf(output, "    }\n");
        fprintf(output, "  }%s\n", (i == conf->all_chars.count - 1) ? "" : ","); 
    }

    // 4. End JSON array and close file
    fprintf(output, "]\n");
    fclose(output);
    free(final_output_path);
}

// --- CLI ARGUMENT PARSER (minimalist, only checks for -o) ---
void parse_cli_args(int argc, char *argv[], t_config *conf) {
    if (argc >= 3 && strcmp(argv[1], "-o") == 0) {
        conf->output_filepath = argv[2];
    }
}


// --- JSON OUTPUT FUNCTION (Individual File) ---

void output_json(const char* charname, const char* accountname, struct filebuf* charsave_fb, struct filebuf* charinfo_fb, struct stats* item_stats, t_config *conf) {
    
    FILE *output = NULL; 
    
    if (conf->output_filepath) {
        output = fopen(conf->output_filepath, "w");
        if (output == NULL) {
            fprintf(stderr, "Error: Cannot open output file %s: %s\n", conf->output_filepath, strerror(errno));
            return;
        }
    }

    t_d2charinfo_header *charinfo_h = (charinfo_fb != NULL) ? (t_d2charinfo_header*)charinfo_fb->buf : NULL;
    
    unsigned char level = *(unsigned char*)(charsave_fb->buf + D2S_LEVEL_OFFSET);
    unsigned char class_id = *(unsigned char*)(charsave_fb->buf + D2S_CLASS_OFFSET);

    fprintf(output, "{\n");
    fprintf(output, "  \"character_info\": {\n");
    
    fprintf(output, "    \"name\": \"%s\",\n", 
        (charinfo_h != NULL) ? (char*)charinfo_h->charname : charname);
    fprintf(output, "    \"account_name\": \"%s\",\n", 
        (charinfo_h != NULL) ? (char*)charinfo_h->account : accountname);
    
    fprintf(output, "    \"level\": %d,\n", level);
    fprintf(output, "    \"class\": \"%s\"\n", get_char_class(class_id)); 
    
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
        // printf("JSON output successfully written to %s\n", conf->output_filepath); // Commented out to reduce console spam
        fclose(output);
    }
}


// --- OTHER UTILITY FUNCTIONS ---

void print_char_info(const char* charname, const char* accountname, struct filebuf* mybuf, t_config *conf) {
    // Simplified this function as it is not strictly necessary in the final JSON-only mode.
}

// (print_stats is removed as it is not needed in the JSON-only mode)

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
