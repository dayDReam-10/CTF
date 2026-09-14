#include <stddef.h>
#include <stdint.h>

#define RC4_STATE_SIZE 256

int rc4_prga(uint8_t state[RC4_STATE_SIZE], uint8_t *data, size_t data_length)
{

	size_t offset;
	uint8_t i = 0;
	uint8_t j = 0;

	if (state == NULL || (data == NULL && data_length != 0)) {
		return -1;
	}

	for (offset = 0; offset < data_length; ++offset) {
		uint8_t swap;
		uint8_t keystream_byte;

		i = (uint8_t)(i + 1);
		j = (uint8_t)(j + state[i]);

		swap = state[i];
		state[i] = state[j];
		state[j] = swap;

		keystream_byte = state[(uint8_t)(state[i] + state[j])];
		data[offset] ^= keystream_byte;
	}

	return 0;
}
