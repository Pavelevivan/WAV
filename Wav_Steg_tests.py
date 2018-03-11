import unittest
from WavSteg import WavSteganography as w


class UnitTests(unittest.TestCase):
    def test_on_1_lsb(self):
        injection = bytes([0b11100110])
        data = bytes([0] * 8)
        injected = w.rewrite_hiding_data(data, 1, injection, 1)
        expected = bytes([1, 1, 1, 0, 0, 1, 1, 0])
        self.assertEqual(injected, expected)
        self.assertEqual(w.eject(injected, 1, 1), injection)

    def test_on_2_lsb(self):
        injection = bytes([0b11100110])
        data = bytes([0]* 8)
        injected = w.rewrite_hiding_data(data, 1, injection, 2)
        expected = bytes([11, 10, 1, 10])
        self.assertEqual(expected, injected)
        self.assertEqual(w.eject(injected, 1, 1), injection)

    def test_on_4_lsb(self):
        injection = bytes([0b11100110])
        data = bytes([0] * 2)
        injected = w.rewrite_hiding_data(data, 1, injection, 4)
        expected = bytes([1110, 110])
        self.assertEqual(expected, injected)
        self.assertEqual(w.eject(injected, 1, 4), injection)

    def test_2_bytes_sample(self):
        injection = bytes([0b01101100])
        data = bytes([0] * 16)
        injected = w.rewrite_hiding_data(data, 2, injection, 1)
        expected = bytes([0, 0,
                          0, 0,
                          1, 0,
                          1, 0,
                          0, 0,
                          1, 0,
                          1, 0,
                          0, 0])
        self.assertEqual(injected, expected)
        self.assertEqual(w.eject(injected, 2, 1), injection)


if __name__ == '__main__':
    unittest.main()
