#ifndef ANTIDEBUG_H
#define ANTIDEBUG_H

#include <unistd.h>
#include <stdio.h>

#define ANTI_DEBUG_TRAP_ADDRESS 0xFE

static volatile int anti_debug_detected;

static void anti_debug_trap(void)
{
	puts("Please wait 1 minute, your flag will be here soon.");
	sleep(60);
	puts("Bye-bye.");
    sleep(5);
	_exit(1);
}

static int is_debugged(void)
{
	FILE *status = fopen("/proc/self/status", "r");
	char line[64];
	unsigned int tracer_pid = 0;
	if (!status) return 0;
	while (fgets(line, sizeof(line), status) &&
	       sscanf(line, "TracerPid:\t%u", &tracer_pid) != 1);
	fclose(status);
	return tracer_pid != 0;
}

__attribute__((constructor(101)))
static void antidebug_init(void) { anti_debug_detected = is_debugged(); }

#endif
