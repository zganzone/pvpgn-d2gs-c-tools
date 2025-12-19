#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define ITEM_LIST_MARKER "JM" // Маркерът, който търсим в D2S файла

int scan_binary_file(const char *filename) {
    FILE *file;
    // Дефинираме буфер, който да побере 2 байта + 1 за терминиращата нула
    char buffer[3]; 
    int byte_offset = 0;
    int matches = 0;

    // 1. Отваряне на файла в БИНАРЕН режим ("rb" - read binary)
    file = fopen(filename, "rb");

    if (file == NULL) {
        fprintf(stderr, "Error: Не мога да отворя бинарен файл '%s'.\n", filename);
        return EXIT_FAILURE;
    }

    printf("--- Сканиране на бинарен файл '%s' за маркера 'JM' ---\n", filename);

    // 2. Четене байт по байт
    // Започваме с четене на първия байт
    if (fread(&buffer[0], 1, 1, file) != 1) {
        // Файлът е празен или има грешка
        fclose(file);
        printf("Файлът е празен.\n");
        return EXIT_SUCCESS;
    }
    
    // Продължаваме да четем, докато не стигнем края на файла
    while (fread(&buffer[1], 1, 1, file) == 1) {
        // Вече имаме буфер[0] и току-що прочетения буфер[1]

        // 3. Проверяваме дали текущите два байта съвпадат с маркера "JM"
        if (buffer[0] == ITEM_LIST_MARKER[0] && buffer[1] == ITEM_LIST_MARKER[1]) {
            printf("Намерен маркер 'JM' на бинарен отместване (offset): %d\n", byte_offset);
            matches++;
        }

        // Преместваме втория байт на първа позиция за следващата итерация
        buffer[0] = buffer[1];
        byte_offset++;
    }
    
    printf("--- Край на сканирането. Общо намерени 'JM' маркери: %d ---\n", matches);

    // 4. Затваряне
    fclose(file);
    
    return EXIT_SUCCESS;
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Употреба: %s <име_на_бинарен_файл>\n", argv[0]);
        printf("Пример: %s /usr/local/pvpgn/var/pvpgn/charsave/tesla\n", argv[0]);
        return EXIT_FAILURE;
    }

    return scan_binary_file(argv[1]);
}
