from pathlib import Path
import struct
import tempfile
import unittest
import zipfile

from inspect_package import game_chunks, inspect, pe_machine


def pe(machine=0x8664):
    data = bytearray(128)
    data[:2] = b'MZ'
    struct.pack_into('<I', data, 60, 64)
    data[64:68] = b'PE\0\0'
    struct.pack_into('<H', data, 68, machine)
    return bytes(data)


def form(payload):
    return b'FORM' + struct.pack('<I', len(payload)) + payload


class PackageTests(unittest.TestCase):
    def test_machine_and_bad_offsets(self):
        self.assertEqual(pe_machine(pe()), 'x64')
        self.assertEqual(pe_machine(pe(0x14c)), 'x86')
        for value in (b'', b'MZ', b'MZ' + bytes(62)):
            with self.assertRaises(ValueError):
                pe_machine(value)

    def test_chunk_bounds(self):
        self.assertEqual(game_chunks(form(b'CODE' + struct.pack('<I', 4) + bytes(4))),
                         [{'name': 'CODE', 'size': 4}])
        for value in (form(b'CODE'), form(b'CODE' + struct.pack('<I', 99)), form(b'') + b'x'):
            with self.assertRaises(ValueError):
                game_chunks(value)

    def test_manifest_does_not_hide_x86_binary(self):
        manifest = '''<Package xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10">
        <Identity Name="Test" ProcessorArchitecture="x64"/>
        <Dependencies><TargetDeviceFamily Name="Windows.Universal"/></Dependencies>
        <Applications><Application Executable="Runner.exe"/></Applications></Package>'''
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'test.appx'
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr('AppxManifest.xml', manifest)
                archive.writestr('Runner.exe', pe(0x14c))
                archive.writestr('Assets/game.win', form(b''))
            report = inspect(path)
            self.assertEqual(report['structural_problems'], ['Runner.exe is not x64'])
            self.assertFalse(report['signature_verified'])
            self.assertFalse(report['gamefiles']['Assets/game.win']['has_bytecode'])


if __name__ == '__main__':
    unittest.main()
