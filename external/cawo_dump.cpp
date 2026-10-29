// Thin wrapper around the official CaWoSched library (KIT-EAE/CaWoSched, MIT):
// runs one variant with local search and prints validity, cost and start times.
// Usage: cawo_dump <dag.dot> <mapping.txt> <setup.txt> <slackR|pressR>
#include <iostream>
#include <string>
#include <lib/multipleProcessors/multiple_processors.h>

int main(int argc, char** argv) {
  if (argc != 5) { std::cerr << "usage\n"; return 2; }
  MultiMachineSchedulingWithoutFreezing s(argv[1], argv[2], argv[3], 1);
  std::string v = argv[4];
  if (v == "slackR") s.compute_slack_machine_focused(false);
  else s.compute_pressure_machine_focused(false);
  s.greedy_scheduling_with_budget_maintenance_enhanced(true);
  s.LS_machine_focused_fastUpdates(10);
  bool valid = s.is_schedule_valid(true);
  std::cout << "VALID " << valid << "\n";
  std::cout << "COST " << (valid ? (long long)s.getCost() : -1) << "\n";
  s.print_schedule();
  return 0;
}
