# MOSES: Detailed Bird's-Eye View of a Single Round

This document provides a comprehensive breakdown of how a single iteration of the MOSES algorithm works, based on the `runMoses` function in `deme/expand-deme.metta`.

## Overview

MOSES (Meta-Optimizing Semantic Evolutionary Search) is an evolutionary program learner. A single round involves:
1. **Selecting** an exemplar (promising program tree) from the metapopulation
2. **Expanding** that exemplar into a deme (a local neighborhood of similar programs)
3. **Optimizing** the deme using a local search algorithm (e.g., hill climbing)
4. **Merging** the best candidates from the optimized deme back into the metapopulation

---

## High-Level Flow: `runMoses` Function

**Location**: `deme/expand-deme.metta` (lines 58-76)

The main loop `runMoses` orchestrates each round:

```metta
(= (runMoses $maxGen $maxScore $maxCandOutput $metaPop $nExpansion $nDeme ...)
  (if (== $maxGen 0)
    ;; TERMINATION: Return top candidates
    ...
    (let* 
     (
       ;; STEP 1: Expand and optimize deme(s)
       ($optimizedDemes (expandDeme $metaPop ...))
       
       ;; STEP 2: Merge optimized deme(s) into metapopulation
       ($updatedMetaPop (mergeDemes $optimizedDemes ...))
       
       ;; STEP 3: Check termination criteria
       ($topScore (getExemplarCscore (OS.getByIdx 0 $metaPop)))
     )
     (if (cScore>= $topScore $maxScore)
         ;; SUCCESS: Return results
         $resultCandi
         ;; CONTINUE: Recursively call with decremented generation count
         (runMoses (- $maxGen 1) ... $updatedMetaPop ...)
     )
  )
)
```

---

## Phase 1: EXPAND DEME (`expandDeme`)

**Location**: `deme/expand-deme.metta` (lines 30-48)

### Step 1.1: Select Exemplar
**Function**: `selectExemplar($metaPop)`
- **Location**: `metapopulation/exemplar-selection.metta`
- **Purpose**: Chooses a promising program tree (exemplar) from the metapopulation
- **Method**: 
  - If metapopulation is empty → Error
  - If only one exemplar → Return it
  - If multiple → **Roulette wheel selection** using Boltzmann distribution
    - Normalizes penalized scores using temperature (`INV_TEMP = 100/4 = 25`)
    - Higher-scoring exemplars have higher probability of selection
    - But lower-scoring ones still have a chance (exploration vs exploitation)

**Output**: An `Exemplar` containing:
- Tree (program structure)
- DemeId
- Cscore (composite score with raw score, complexity, penalties)
- Bscore (behavioral score - how it behaves on different inputs)

---

### Step 1.2: Extract Tree from Exemplar
**Function**: `getExemplarTree($exemplar)`
- **Location**: `metapopulation/metapopulation.metta` (line 100)
- **Purpose**: Extracts the program tree structure from the exemplar
- **Output**: `Tree` structure representing the program (e.g., `(AND (OR A B) (NOT C))`)

---

### Step 1.3: Create Deme IDs
**Function**: `createDemeIds($nExpansion, $nDeme)`
- **Location**: `deme/deme-id-creation.metta`
- **Purpose**: Generates unique identifiers for the demes to be created
- **Output**: List of `DemeId` values

---

### Step 1.4: Create Deme(s)
**Function**: `createDeme($nDeme, $demeIds, $tree, $itable, ...)`
- **Location**: `deme/create-deme.metta`

**What is a Deme?**
- A **deme** is a population of program instances with the **same structure** (tree) but **different knob settings**
- Think of it as a "neighborhood" around the exemplar tree
- All instances in a deme share the same representation but have different parameter values

**Internal Process**:
1. **Create Representation(s)**: `createRepresentation(...)`
   - **Location**: `representation/create-representation.metta` → calls `representation(...)`
   - **Purpose**: Converts the exemplar tree into a **representation** with "knobs"
   
   **What is a Representation?**
   - A representation adds "knobs" (adjustable parameters) to the tree structure
   - Each knob is at a specific location (NodeId) in the tree
   - Knobs allow creating variations: e.g., at position `(1 2)`, knob 0 = `A`, knob 1 = `B`, knob 2 = `(AND A B)`
   - This is MOSES's key innovation: **structural variation** without changing tree shape
   
   **Representation Creation Steps**:
   1. Extract features from exemplar tree (`treeFtsIndices`)
   2. Apply feature selection algorithm (if specified)
   3. Prune exemplar (if `$prune-exemplar` is True)
   4. For each deme to create:
      - Call `buildKnobs` to add knobs at strategic locations
      - Create `DiscMap` (discrete map: knob locations → knob specifications)
      - Create `DiscKnobMap` (map: NodeId → index in DiscMap)
      - Wrap in `Representation` type
   
2. **Wrap in Deme Structure**: 
   - Each representation is wrapped in a `Deme`:
     - Representation (with knobs)
     - InstanceSet (initially empty - will be populated during optimization)
     - DemeId

**Output**: List of `Deme` structures (one per `$nDeme`), each with:
- A representation (tree + knobs)
- Empty instance set (to be filled during optimization)
- Unique deme ID

---

### Step 1.5: Optimize Deme(s)
**Function**: `optimizeDemes($deme, $truthTableBScore, $inst, $optimize)`
- **Location**: `deme/expand-deme.metta` (lines 9-10)
- **Purpose**: Applies a local optimization algorithm to populate and improve the deme

**What Happens?**
- Calls the optimizer function (e.g., `hillClimbing`, `simulatedAnnealing`, etc.)
- The optimizer:
  1. **Populates** the deme with instances by:
     - Sampling different knob settings
     - Creating program instances from those settings
     - Evaluating them on the training data
  2. **Optimizes** the instances using local search:
     - Explores neighborhood (variations of knob settings)
     - Uses crossover (in some optimizers) to combine good instances
     - Uses mutation to introduce variation
     - Keeps the best instances based on composite scores
  3. Returns an **optimized deme** with scored instances

**Common Optimizers**:
- **Hill Climbing**: `optimization/hillclimbing/` - Local search with crossover
- **Simulated Annealing**: `optimization/simulated-annealing-algo/` - Probabilistic acceptance
- **PGE/SGE**: `optimization/pge/`, `optimization/sge/` - Grammar-based evolution

**Output**: Optimized `Deme` containing:
- Representation (unchanged)
- ScoredInstanceSet (list of (Instance, Cscore) pairs, sorted by score)
- DemeId

---

## Phase 2: MERGE DEMES (`mergeDemes`)

**Location**: `deme/merge-demes.metta` (lines 204-235)

### Purpose
Takes the optimized deme(s) and merges their best candidates into the metapopulation, while maintaining diversity and quality.

### Step 2.1: Sort Instances
**Function**: `sortDeme($sInstList)`
- Sorts scored instances within each deme in **decreasing order** of composite score
- Best instances first

---

### Step 2.2: Keep Top Unique Candidates
**Function**: `keepTopUniqueCandidates($sortedSInstList, $nEval, $maxCandsPerDeme)`
- **Location**: `deme/merge-demes.metta` (lines 33-42)
- **Purpose**: 
  - Removes **adjacent duplicates** (instances with identical structure/score)
  - Limits to top `$nEval` instances, further capped by `$maxCandsPerDeme`
- **Why?**: Prevents the metapopulation from being flooded with duplicate programs

---

### Step 2.3: Trim Down Deme
**Function**: `trimDownDeme($sInstList, $minPoolSize, $complexityTemperature)`
- **Location**: `deme/merge-demes.metta` (lines 72-83)
- **Purpose**: Further filters out low-scoring instances
- **Method**:
  - If deme size ≤ `$minPoolSize` or ≤ 1 → Keep all
  - Otherwise:
    - Calculate bottom score threshold: `topScore - usefulScoreRange($complexityTemperature)`
    - Remove instances with penalized score below threshold
- **Why?**: Maintains quality while allowing some diversity

---

### Step 2.4: Convert Instances to Trees (Exemplars)
**Function**: `demeToTrees($deme, $itable)`
- **Location**: `deme/merge-demes.metta` (lines 91-108)
- **Purpose**: Converts scored instances back into program trees (exemplars)

**Process**:
- For each `ScoredInstance` in the deme:
  1. Extract the instance (knob settings)
  2. Extract the composite score
  3. **Convert instance to tree**: `getCandidate($rep, $inst)`
     - Uses the representation to map knob settings back to tree structure
     - This "decodes" the instance into an actual program tree
  4. **Compute behavioral score**: `scoreTree($itable, $tree)`
     - Evaluates how the tree behaves on different input patterns
     - Creates a behavioral signature (important for diversity)
  5. Wrap in `Exemplar` structure: (Tree, DemeId, Cscore, Bscore)

**Output**: List of `Exemplar` objects ready for metapopulation

---

### Step 2.5: Filter New Candidates
**Function**: `getNewCandidates($candidates, $metaPop)`
- **Location**: `deme/merge-demes.metta` (lines 116-118+)
- **Purpose**: Removes exemplars that are **already in the metapopulation**
- **Why?**: Prevents duplicate programs in the metapopulation
- **Method**: For each candidate, checks if an equivalent exemplar exists in metaPop (tree structure comparison)

---

### Step 2.6: Remove Dominated Exemplars
**Function**: `removeDominated($candidates)`
- **Location**: `deme/merge-demes.metta` (lines 156-176)
- **Purpose**: Applies **Pareto dominance** filtering
- **Method**:
  - An exemplar A **dominates** B if:
    - A's behavioral score is better or equal on ALL dimensions
    - A's behavioral score is strictly better on AT LEAST ONE dimension
  - Removes exemplars that are dominated by others
- **Why?**: Maintains diversity - keeps exemplars that excel in different ways

---

### Step 2.7: Merge Candidates into Metapopulation
**Function**: `mergeCandidates($candidates, $metapop)`
- **Location**: `deme/merge-demes.metta` (lines 185-188)
- **Purpose**: Inserts new exemplars into the metapopulation
- **Method**:
  - Uses `OS.insert` with `compareExemplar` comparator
  - Metapopulation is an **ordered set** (sorted by:
    1. Penalized score (higher is better)
    2. Complexity (lower is better) - tie breaker
  )
  - Maintains sorted order automatically

---

### Step 2.8: Resize Metapopulation
**Function**: `resizeMetapop($updatedMetaPop, $nToKeep, $minPoolSize, ...)`
- **Location**: `metapopulation/metapopulation.metta` (line 17+)
- **Purpose**: Controls metapopulation size to balance memory and diversity
- **Method**:
  - Protects top `$nToKeep` exemplars from removal
  - Ensures at least `$minPoolSize` exemplars remain
  - Uses `$complexityTemperature` and `$capCoef` to determine maximum size
  - Removes excess exemplars from the bottom (worst scores)

---

## Phase 3: TERMINATION CHECK

Back in `runMoses`:

1. **Check Generation Count**: If `$maxGen == 0` → Return top `$maxCandOutput` candidates
2. **Check Score Threshold**: If top exemplar's score ≥ `$maxScore` → Return results
3. **Otherwise**: Recursively call `runMoses` with:
   - Decremented `$maxGen`
   - Updated metapopulation
   - Same other parameters

---

## Key Concepts Summary

### Exemplar
- A scored program tree
- Contains: Tree structure, Composite score, Behavioral score, DemeId

### Deme
- A local population of program instances
- All share the same representation (tree structure with knobs)
- Differ only in knob settings
- Optimized using local search

### Representation
- A tree structure augmented with "knobs" (adjustable parameters)
- Allows creating variations without changing tree shape
- Core innovation of MOSES

### Metapopulation
- Global collection of diverse, high-quality exemplars
- Maintained as an ordered set (sorted by score, then complexity)
- Source of exemplars for new demes

### Instance
- A specific setting of all knobs in a representation
- When "decoded" via `getCandidate`, becomes a program tree

---

## Data Flow Diagram

```
Metapopulation (Ordered Set of Exemplars)
    ↓
[Select Exemplar] → Exemplar
    ↓
[Extract Tree] → Tree
    ↓
[Create Representation] → Representation (Tree + Knobs)
    ↓
[Create Deme] → Deme (Representation + Empty InstanceSet + DemeId)
    ↓
[Optimize Deme] → Optimized Deme (Representation + ScoredInstanceSet + DemeId)
    ↓
[Sort & Deduplicate] → Sorted Unique Instances
    ↓
[Trim] → Filtered High-Quality Instances
    ↓
[Convert to Trees] → List of Exemplars
    ↓
[Filter New] → New Exemplars (not in metaPop)
    ↓
[Remove Dominated] → Non-dominated Exemplars
    ↓
[Merge] → Updated Metapopulation (with new exemplars inserted)
    ↓
[Resize] → Final Metapopulation (size-controlled)
    ↓
[Termination Check] → Continue or Return Results
```

---

## File Locations for Key Functions

| Function | File | Purpose |
|----------|------|---------|
| `runMoses` | `deme/expand-deme.metta` | Main loop |
| `expandDeme` | `deme/expand-deme.metta` | Expand and optimize demes |
| `selectExemplar` | `metapopulation/exemplar-selection.metta` | Select exemplar from metaPop |
| `getExemplarTree` | `metapopulation/metapopulation.metta` | Extract tree from exemplar |
| `createDeme` | `deme/create-deme.metta` | Create deme structure |
| `createRepresentation` | `representation/create-representation.metta` | Create representation |
| `representation` | `representation/representation.metta` | Build representation with knobs |
| `optimizeDemes` | `deme/expand-deme.metta` | Call optimizer |
| `mergeDemes` | `deme/merge-demes.metta` | Merge demes into metaPop |
| `demeToTrees` | `deme/merge-demes.metta` | Convert instances to exemplars |
| `getCandidate` | `representation/representation.metta` | Convert instance to tree |
| `resizeMetapop` | `metapopulation/metapopulation.metta` | Control metaPop size |

---

This completes one round of MOSES. The process repeats until termination criteria are met.
