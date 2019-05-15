# ESTCP
code for ESTCP analysis/ generator &amp; BESS reliability
[data] -Final_out.xlsx :  output data files
Each column label describes the case assumptions
-	Gens Only….   Generators only, no PV system included to duplicate ‘Variable Load’ simulation ESTCP provided
-	Gens and PV Array…  generators + PV array reducing critical load. But no batteries
-	Gens and PV Array 130%...   critical load increased by 30%, no batteries
-	Other cols, eg fuel0 scalefactor 1 genunits7 batsize 375.0 bat units 1  
o	Fuel0 means generators had fuel, Fuel1 means generators had no fueld
o	Scalefactor 1 (base case), scalefactor 1.3 (130% critical load case)
o	Genunitsn  # of gen units (at whatever size the facility specifies)
o	Batsize xxxx  power capacity of battery, bat units n # batteries

Python dependencies:
Numpy, pandas, scipy.special, numba [numba is a vectorizer/ compiler for accelerating numerical calculations]

Estcprun.py: automatated scenario creator. It details assumptions (eg. mtbf for generators and energy storage, failure to start probabilities Pfr etc.)

Workflow:

Scenario definition
It defines lists of scenarios to run: eg. batno = [1, 2] includes scenarios with 1 or 2 battery units, batsizes = [0.5, 1] defines scenarios where the battery size is either 50% or 100% of the generator unit size, scalefacs = [1, 1.3] scales the critical load by 1 (no change) or by 1.3 (130% scenario case ESTCP requested)

No PV Case
Calculates coverage of load probability (COLP) for Gen only case

PV Case
COLP calculated including PV but no batteries

PV Case 130% critical load
COLP calculated including PV but no batteries, 130% critical load

Battery Scenarios
Nested loops calculating COLP for all battery scenarios including “no fuel” cases

Calculation
No batteries: genfail_func.readin (no PV case) or genfail_pv_func.readin (PV case) reads in generator data and metered load data, performs monte carlo simulation (MCS) of generator failures to start and failures to run and produces failure matrix (niteration, 8760, 168) whose value is ‘1’ everywhere critical load exceeded available generation; ’failfind’ then consolidates the failure matrix so that any hour a ‘1’ appears is extended to the end of the 168 hour simulation period (reproducing the logic that once a fail occurs that simulation ends). The niterations x 8760 scenarios are averaged into a single 168 hour-long column giving the resulting failure probability

Batteries: genfail_pv_func_nunits reads in generator & metered load data, performs monte carlo simulation (MCS) of generator failures to start and failures to run and calculates unserved load usl (niteration, 8760, 168) whose value is positive everywhere critical load exceeded available generation but negative whenever generator capacity exists for recharging the batteries. Failfindbat analyzes the usl, determining where sufficient battery capacity exists to cover usl (or charges batteries with excess generator capacity), then averages net matrix of resulting failures, calculating colp.


Genfail 
First determines, per (niterations, 8760) scenario which generators failed to start. It calculates a random # for each scenario initial timepoint, for each generator. Whenever the random # < Pfs that generator is failed. It sums the # of active generators at each initial timepoint for each scenario

Failure to run is handled differently: at time t the algorithm computes the probability p that 1 generator may fail and the probability that 2 generators may fail following equation (8) of the ESTCP notes. That is, it calculates the transition probability g g-1  and g g-2. Then it generators random #’s where, if they are smaller than these transition probabilities, the # of generators is decremented.

With the # of generators available at each timepoint the unserved load and failure case (for no battery cases) can be calculated for each scenario timepoint (niterations, 8760, 168) hours.

Failfind
Analyzes the failure matrix (niterations, 8760, 168) and extends any failure (a ‘1’) in time along the 3rd matrix dimension (168 timepoints) then averages all the scenarios. Numba accelerator shortens the runtime from ~30 minutes to ~2 seconds using @njit indication to compile python into machine code

Failfindbat
Analyzes usl. Computes a failure matrix wherever battery charge or capacity can’t cover usl. It charges battery with that portion of the generator capacity not needed for the critical load, less a penalty for the battery round trip efficiency.
