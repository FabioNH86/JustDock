#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
	if (argc != 2) {
		return 1;
	}
	int n = atoi(argv[1]);
	printf("1");
	for(int i=2; i<=n; i++) {
		printf(",%d", i);
	}
	return 0;
}
