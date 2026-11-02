// Adapter wrapper for the official CWM code (KIT-EAE/CWM, MIT).
// Usage: cwm_dump <dag> <cluster.json> <variant-name> <profile.json> <CWM variant> <deadline>
// Prints VALID, MAKESPAN, COST and one "T <task> <start> <end> <proc>" line per task.
#include <iostream>
#include <string>
#include <algorithms/mapper.hpp>
int main(int argc, char** argv) {
  if (argc != 7) { std::cerr << "usage\n"; return 2; }
  const unsigned int deadline = std::stoul(argv[6]);
  CaWoMap CWM(argv[1], argv[2], argv[3], argv[4], 42);
  CWM.prepare_HEFT_SL();
  Schedule schedule = CWM.CaWoMap_Init(argv[5]);
  CWM.guarantee_deadline_routine(schedule, deadline);
  bool ok = CWM.final_correctness() && CWM.check_deadline(deadline);
  std::cout << "VALID " << ok << "\n";
  std::cout << "MAKESPAN " << CWM.compute_final_makespan() << "\n";
  std::cout << "COST " << CWM.final_compute_carbon_cost_fast() << "\n";
  const auto& t = CWM.get_final_times(); const auto& p = CWM.get_final_procs();
  for (size_t i = 0; i < t.size(); ++i) std::cout << "T " << i << " " << t[i].first << " " << t[i].second << " " << p[i] << "\n";
  return 0;
}
