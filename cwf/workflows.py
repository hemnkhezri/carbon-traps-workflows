"""WfCommons workflow instances, runtimes scaled to a target HEFT makespan."""
import random

import numpy as np
import wfcommons.wfchef.recipes as R
from wfcommons import WorkflowGenerator

from .sched import Instance, heft

# (label, recipe, requested tasks)
SPECS = [
    ("montage-s", R.MontageRecipe, 200),
    ("montage-l", R.MontageRecipe, 400),
    ("epigenomics", R.EpigenomicsRecipe, 300),
    ("blast", R.BlastRecipe, 300),
    ("bwa", R.BwaRecipe, 300),
    ("cycles", R.CyclesRecipe, 300),
    ("1000genome", R.GenomeRecipe, 300),
    ("seismology", R.SeismologyRecipe, 300),
    ("soykb", R.SoykbRecipe, 300),
    ("srasearch", R.SrasearchRecipe, 300),
]


def build_raw(recipe, n, seed):
    random.seed(seed)
    np.random.seed(seed)
    tries = [n, 400, 500, 700, 1000]
    last = None
    for k in tries:
        try:
            w = WorkflowGenerator(recipe.from_num_tasks(k)).build_workflow()
            break
        except Exception as e:  # recipe minimum size not met
            last = e
    else:
        raise last
    names = list(w.nodes)
    idx = {nm: i for i, nm in enumerate(names)}
    rt = np.array([max(float(w.tasks[nm].runtime or 0.0), 1.0) for nm in names])
    preds = [[idx[p] for p in w.predecessors(nm)] for nm in names]
    succs = [[idx[s] for s in w.successors(nm)] for nm in names]
    return names, rt, preds, succs


def scaled_instance(raw, P, target_min):
    names, rt, preds, succs = raw
    scale = 1.0
    for _ in range(4):
        dur = np.maximum(1, np.round(rt * scale / 60.0)).astype(int)
        inst = Instance(names, dur, preds, succs)
        H = int(dur.sum()) + 10
        M = int(max(heft(inst, P, H) + inst.dur))
        if abs(M - target_min) <= 0.02 * target_min:
            break
        scale *= target_min / M
    return inst, M
