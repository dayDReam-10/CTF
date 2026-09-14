/* Standard RC4 Key-Scheduling Algorithm (KSA). */
#include <stddef.h>
#include <stdint.h>

#define RC4_STATE_SIZE 256

int rc4_ksa(uint8_t state[RC4_STATE_SIZE], const uint8_t *key, size_t key_length)
{
	size_t i;
	uint8_t j = 0;

	if (state == NULL || key == NULL || key_length == 0) {
		return -1;
	}

	for (i = 0; i < RC4_STATE_SIZE; ++i) {
		state[i] = (uint8_t)i;
	}

	for (i = 0; i < RC4_STATE_SIZE; ++i) {
		size_t key_index = i % key_length;
		uint8_t swap;

		j = (uint8_t)(j + state[i] + key[key_index]);
		swap = state[i];
		state[i] = state[j];
		state[j] = swap;
	}

	return 0;
}
