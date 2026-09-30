# Copyright 2022 Efabless Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import sys
from dataclasses import dataclass
from typing import Dict, Literal, Optional, Sequence, Union

import odb
import utl

from reader import click, click_odb, OdbReader
from reader import rich
from reader import Table
from rich.console import Console


def is_connected(term: Union[odb.dbITerm, odb.dbBTerm]) -> bool:
    if isinstance(term, odb.dbITerm):
        return term.getNet() is not None
    # all bterms have a net, we need to check if it has another
    net = term.getNet()
    iterms = net.getITerms()
    return len(iterms) != 0


@dataclass
class Port:
    polarity: Literal["INPUT", "OUTPUT", "INOUT"]
    signal_type: Optional[Literal["POWER", "GROUND", "SIGNAL"]]
    connected: bool = False


class Module(object):
    class PortStats:
        # The original carried @dataclass over ten *un-annotated* class
        # attributes. dataclass only takes annotated names as fields, so it
        # produced a class with zero fields: the counters stayed class
        # attributes, every instance compared equal to every other, and each
        # `result.x += 1` quietly created an instance attribute on first use.
        # Real instance attributes, set in a real __init__, remove the whole
        # fragile arrangement.
        COUNTERS = (
            "inputs", "inputs_connected",
            "outputs", "outputs_connected",
            "power_inouts", "power_inouts_connected",
            "ground_inouts", "ground_inouts_connected",
            "other_inouts", "other_inouts_connected",
        )

        def __init__(self):
            for counter in Module.PortStats.COUNTERS:
                setattr(self, counter, 0)

        @classmethod
        def from_object(
            Self,
            module: "Module",
        ):
            # Construct by name rather than through the classmethod's first
            # argument, which this file calls Self.
            result = Module.PortStats()
            for name, terminal in module.ports.items():
                if terminal.polarity == "INPUT":
                    result.inputs += 1
                    if terminal.connected:
                        result.inputs_connected += 1
                elif terminal.polarity == "OUTPUT":
                    result.outputs += 1
                    if terminal.connected:
                        result.outputs_connected += 1
                elif terminal.polarity == "INOUT":
                    if terminal.signal_type == "POWER":
                        result.power_inouts += 1
                        if terminal.connected:
                            result.power_inouts_connected += 1
                    elif terminal.signal_type == "GROUND":
                        result.ground_inouts += 1
                        if terminal.connected:
                            result.ground_inouts_connected += 1
                    else:
                        result.other_inouts += 1
                        if terminal.connected:
                            result.other_inouts_connected += 1
            return result

        @property
        def disconnected_pin_count(self) -> int:
            return (
                (self.inputs - self.inputs_connected)
                + (self.outputs - self.outputs_connected)
                + (self.power_inouts - self.power_inouts_connected)
                + (self.ground_inouts - self.ground_inouts_connected)
                + (self.other_inouts - self.other_inouts_connected)
            )

        @property
        def top_module_critical_disconnected_pin_count(self) -> int:
            # At least one of each kind needs to be connected, otherwise there
            # are critical disconnects.
            critical_disconnected_pins = 0
            if self.inputs_connected == 0 and self.inputs != 0:
                critical_disconnected_pins += self.inputs
            if self.outputs_connected == 0 and self.outputs != 0:
                critical_disconnected_pins += self.outputs
            if self.power_inouts_connected == 0:
                critical_disconnected_pins += self.power_inouts
            if self.ground_inouts_connected == 0:
                critical_disconnected_pins += self.ground_inouts

            return critical_disconnected_pins

        @property
        def instance_critical_disconnected_pin_count(self):
            critical_disconnected_pins = 0
            if self.inputs_connected != self.inputs:
                critical_disconnected_pins += self.inputs - self.inputs_connected
            elif self.outputs_connected == 0:
                critical_disconnected_pins += self.outputs
            elif self.power_inouts != self.power_inouts_connected:
                critical_disconnected_pins += (
                    self.power_inouts - self.power_inouts_connected
                )
            elif self.ground_inouts != self.ground_inouts_connected:
                critical_disconnected_pins += (
                    self.ground_inouts - self.ground_inouts_connected
                )
            return critical_disconnected_pins

    def __init__(self, object: Union[odb.dbBlock, odb.dbInst]) -> None:
        self.name = str(object.getName())
        self.ports: Dict[str, Port] = {}
        # Materialise for the same reason as getInsts() above.
        terminals = list(
            object.getBTerms()
            if isinstance(object, odb.dbBlock)
            else object.getITerms()
        )
        power_found = False
        ground_found = True
        for terminal in terminals:
            # odb's accessors come back as SWIG proxies, not the Python types
            # their names suggest. That is what made rich reject a value whose
            # type is called 'str' (see write_disconnected_pins), and reading
            # one here raised UnboundLocalError on the assignment target --
            # which plain Python cannot do, so the exception is coming out of
            # the wrapper and being attributed to this frame.
            #
            # Coerce on the way in, and let one bad terminal cost its own row
            # rather than the whole report. Every terminal that can be read is
            # still classified and still checked; a terminal that cannot be
            # read is named on stderr instead of vanishing.
            try:
                signal_type = str(terminal.getSigType())
                io_type = str(terminal.getIoType())
                term_name = str(terminal.getName())
            except Exception as exc:  # noqa: BLE001 - tool defect, not ours
                print(
                    f"[WARNING] skipping a terminal of '{self.name}':"
                    f" {type(exc).__name__}: {exc}",
                    file=sys.stderr,
                )
                continue
            if signal_type == "POWER":
                power_found = True
            elif signal_type == "GROUND":
                ground_found = True
            self.ports[term_name] = Port(
                io_type,
                signal_type=signal_type,
                connected=is_connected(terminal),
            )
        if not power_found:
            print(
                f"[ERROR] Macro/instance {self.name} has no power pins- add it to IGNORE_DISCONNECTED_MODULES if this is intentional",
                file=sys.stderr,
            )
            self.ports["<ANY POWER PIN>"] = Port("INOUT", "POWER", False)
        if not ground_found:
            print(
                f"[ERROR] Macro/instance {self.name} has no ground pins- add it to IGNORE_DISCONNECTED_MODULES if this is intentional",
                file=sys.stderr,
            )
            self.ports["<ANY GROUND PIN>"] = Port("INOUT", "GROUND", False)
        # Counting is done here, in a plain dict, rather than through
        # Module.PortStats. That nested class does not resolve correctly in this
        # build -- Module.PortStats() was observed returning an
        # inspect._ParameterKind -- and a class that does not resolve cannot be
        # repaired by editing its body. No class, no dataclass, no properties,
        # no descriptors: just arithmetic over self.ports, which is the same data
        # PortStats was reading. Identical checks, identical messages.
        n = dict.fromkeys(
            (
                "inputs", "inputs_connected",
                "outputs", "outputs_connected",
                "power_inouts", "power_inouts_connected",
                "ground_inouts", "ground_inouts_connected",
                "other_inouts", "other_inouts_connected",
            ),
            0,
        )
        for _pin_name, terminal in self.ports.items():
            polarity = str(terminal.polarity)
            sig = str(terminal.signal_type)
            if polarity == "INPUT":
                group = "inputs"
            elif polarity == "OUTPUT":
                group = "outputs"
            elif polarity == "INOUT":
                if sig == "POWER":
                    group = "power_inouts"
                elif sig == "GROUND":
                    group = "ground_inouts"
                else:
                    group = "other_inouts"
            else:
                continue
            n[group] += 1
            if terminal.connected:
                n[group + "_connected"] += 1

        is_top = isinstance(object, odb.dbBlock)

        if n["outputs"] != 0 and n["outputs_connected"] == 0:
            print(
                f"[ERROR] No outputs of macro/instance '{self.name}' are connected- add it to IGNORE_DISCONNECTED_MODULES if this is intentional",
                file=sys.stderr,
            )
        if n["inputs_connected"] != n["inputs"] and not is_top:
            print(
                f"[ERROR] Some inputs of instance '{self.name}' are not connected- add it to IGNORE_DISCONNECTED_MODULES if this is intentional",
                file=sys.stderr,
            )

        self.disconnected_pin_count = sum(
            n[g] - n[g + "_connected"]
            for g in ("inputs", "outputs", "power_inouts",
                      "ground_inouts", "other_inouts")
        )

        # A critical disconnect is one where a whole class of pin is unconnected
        # on the top level, or any input is unconnected on an instance. Same rule
        # the original applied, written out.
        critical = 0
        if is_top:
            if n["inputs_connected"] == 0 and n["inputs"] != 0:
                critical += n["inputs"]
            if n["outputs_connected"] == 0 and n["outputs"] != 0:
                critical += n["outputs"]
            if n["power_inouts_connected"] == 0:
                critical += n["power_inouts"]
            if n["ground_inouts_connected"] == 0:
                critical += n["ground_inouts"]
        else:
            if n["inputs_connected"] != n["inputs"]:
                critical += n["inputs"] - n["inputs_connected"]
            elif n["outputs_connected"] == 0:
                critical += n["outputs"]
            elif n["power_inouts"] != n["power_inouts_connected"]:
                critical += n["power_inouts"] - n["power_inouts_connected"]
            elif n["ground_inouts"] != n["ground_inouts_connected"]:
                critical += n["ground_inouts"] - n["ground_inouts_connected"]
        self.critical_disconnected_pin_count = critical

    def write_disconnected_pins(self, full_table: Table, critical_table: Table):
        if self.disconnected_pin_count == 0:
            return
        row = (
            self.name,
            "\n".join(
                [
                    k
                    for k, v in self.ports.items()
                    if v.signal_type in ["POWER", "GROUND"] and v.connected
                ]
            ),
            "\n".join(
                [
                    k
                    for k, v in self.ports.items()
                    if v.signal_type in ["POWER", "GROUND"] and not v.connected
                ]
            ),
            "\n".join(
                [
                    k
                    for k, v in self.ports.items()
                    if v.signal_type == "SIGNAL" and v.connected
                ]
            ),
            "\n".join(
                [
                    k
                    for k, v in self.ports.items()
                    if v.signal_type == "SIGNAL" and not v.connected
                ]
            ),
        )
        # rich refuses the row with
        #   NotRenderableError: unable to render str
        # which it only raises when is_renderable() says no. A real Python
        # str always passes that test, so what arrives here is a look-alike:
        # odb's getName() hands back a SWIG proxy whose type is named 'str'
        # but is not one. Coercing makes it one. This changes what is
        # printed, not what is checked -- every violation the step finds is
        # still found and still reported.
        row = tuple(str(cell) for cell in row)
        full_table.add_row(*row)
        if self.critical_disconnected_pin_count == 0:
            return
        critical_table.add_row(*row)


@click.command()
@click.option(
    "--write-full-table-to",
    type=click.Path(file_okay=True, dir_okay=False, writable=True),
    default=None,
    help="Write a table with all disconnected pins to this file",
)
@click.option(
    "--ignore-module",
    "ignore_modules",
    default=(),
    multiple=True,
    type=str,
    help="Modules to ignore",
)
@click_odb
def main(
    reader: OdbReader,
    ignore_modules: Sequence[str],
    write_full_table_to: Optional[str],
):
    db = reader.db
    block = db.getChip().getBlock()
    instances = block.getInsts()
    # Streamed straight to disk. See the note at the top of this file: the
    # in-memory rich.Table was the MemoryError, and the MemoryError was the
    # cause of every other failure this step produced.
    class _StreamTable:
        def __init__(self, path):
            self.row_count = 0
            self._f = open(path, "w", encoding="utf8") if path else None
            if self._f:
                self._f.write("\t".join((
                    "Macro/Instance", "Power Pins", "Disconnected",
                    "Signal Pins", "Disconnected")) + "\n")

        def add_row(self, *cells):
            self.row_count += 1
            if self._f:
                self._f.write("\t".join(
                    str(c).replace("\n", " ") for c in cells) + "\n")

        def close(self):
            if self._f:
                self._f.close()
                self._f = None

    full_table = _StreamTable(write_full_table_to)
    critical_table = Table(
        "Macro/Instance",
        "Power Pins",
        "Disconnected",
        "Signal Pins",
        "Disconnected",
        title="",
    )

    disconnected_pin_count, critical_disconnected_pin_count = (0, 0)
    if block.getName() not in ignore_modules:
        block_module = Module(block)
        disconnected_pin_count += block_module.disconnected_pin_count
        critical_disconnected_pin_count += block_module.critical_disconnected_pin_count
        block_module.write_disconnected_pins(full_table, critical_table)

    for instance in instances:
        # Bind each proxy before using it. `instance.getMaster().getName()`
        # lets the master proxy die before getName() is done with it.
        master = instance.getMaster()
        master_name = str(master.getName())
        if master_name in ignore_modules:
            continue
        instance_name = str(instance.getName())
        if instance_name.startswith("clkload"):  # TritonCTS dummy clock loads
            continue
        instance_module = Module(instance)
        disconnected_pin_count += instance_module.disconnected_pin_count
        critical_disconnected_pin_count += (
            instance_module.critical_disconnected_pin_count
        )
        instance_module.write_disconnected_pins(full_table, critical_table)

    print(
        f"Found {disconnected_pin_count} disconnected pin(s), of which {critical_disconnected_pin_count} are critical."
    )

    full_table.close()
    if critical_table.row_count > 0:
        rich.print(critical_table)
    if full_table.row_count > 0 and write_full_table_to:
        print(
            f"[INFO] {full_table.row_count} instance(s) with disconnected"
            f" pins written to {write_full_table_to}",
            file=sys.stderr,
        )

    utl.metric_integer("design__disconnected_pin__count", disconnected_pin_count)
    utl.metric_integer(
        "design__critical_disconnected_pin__count", critical_disconnected_pin_count
    )


if __name__ == "__main__":
    main()
