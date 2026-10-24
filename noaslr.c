#define _GNU_SOURCE
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <sys/personality.h>
#include <unistd.h>

int main(int argc, char **argv) {
  int current;
  if (argc < 2) {
    fprintf(stderr, "usage: noaslr PROGRAM [ARG ...]\n");
    return 64;
  }
  current = personality(0xffffffffUL);
  if (current == -1) {
    fprintf(stderr, "personality(read): %s\n", strerror(errno));
    return 1;
  }
  if (personality((unsigned long)current | ADDR_NO_RANDOMIZE) == -1) {
    fprintf(stderr, "personality(ADDR_NO_RANDOMIZE): %s\n", strerror(errno));
    return 1;
  }
  execvp(argv[1], &argv[1]);
  fprintf(stderr, "execvp(%s): %s\n", argv[1], strerror(errno));
  return 1;
}
