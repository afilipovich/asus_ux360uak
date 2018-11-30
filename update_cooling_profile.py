#!/usr/bin/env python

"""Tweak cooling profile to keep cooling fan quiet when laptop is idle.

Do this by rewriting thermal tipping points in Embedded Controller memory via ACPI.
Requires "acpi_call" kernel module to be loaded.
"""

import subprocess
import logging as log
log.basicConfig(format='%(asctime)s %(levelname)s %(process)d %(processName)s %(message)s', level=log.INFO)


class ThermalTable:
    offset = 0x537
    default_tipping_points = [35, 40, 45, 50, 55, 60, 65, 80]
    quiet_tipping_points = [48, 50, 53, 57, 61, 65, 70, 80]

    def call_acpi(self, command):
        with open('/proc/acpi/call', 'w') as acpi_call:
            log.info(command)
            acpi_call.write(command)
            acpi_call.close()
        with open('/proc/acpi/call') as acpi_call:
            response = acpi_call.read()
            acpi_call.close()
        return response

    def update_table(self, tipping_points):
        assert len(tipping_points) <= 8
        for i, t in enumerate(tipping_points):
            addr = self.offset + i
            cmd = '\_SB.PCI0.LPCB.EC0.WRAM {} {}'.format(hex(addr), hex(t))
            self.call_acpi(cmd)

    def read_value(self, addr):
        cmd = '\_SB.PCI0.LPCB.EC0.RRAM {}'.format(hex(addr))
        r = self.call_acpi(cmd)
        r = int(r.split('\00')[0], 16)
        return r

    def set_quiet_profile(self):
        log.info('Setting quiet cooling profile. It may take a few minutes for it to become active.')
        self.update_table(self.quiet_tipping_points)

    def set_default_profile(self):
        log.info('Setting default cooling profile.')
        self.update_table(self.default_tipping_points)

    def is_flipped(self):
        log.info(self.read_value(0x51d))
        return bool(self.read_value(0x51d))

    def set_flip_mode(self):
        flipped = self.is_flipped()
        log.info("Flipped: %s", flipped)
        self.xinput('ELAN1300:00 04F3:3028 Touchpad', not flipped)
        self.xinput('FTSC1000:00 2808:5120', flipped)

    def xinput(self, device, enable):
        action = "enable" if enable else "disable"
        cmd = [
            "xinput",
            action,
            device,
        ]
        return subprocess.call(cmd)


def main():
    tt = ThermalTable()
    tt.set_quiet_profile()
    tt.set_flip_mode()

if __name__ == '__main__':
    main()
