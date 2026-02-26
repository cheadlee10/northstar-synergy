/**
 * CLIFF TOOL: Variance Decomposition Engine
 * ============================================
 * Takes budget and actual data by facility, decomposes total variance
 * into Volume, Mix, Rate, and component-level drivers.
 *
 * Input: JSON file path as argv[2] with structure:
 * {
 *   "period": "January 2026",
 *   "facilities": [
 *     {
 *       "name": "LAX",
 *       "budget_cost": 200000,
 *       "actual_cost": 218000,
 *       "budget_vol": 50000,
 *       "actual_vol": 53000,
 *       "components": {
 *         "stop_fee": { "budget": 80000, "actual": 88000 },
 *         "b2c": { "budget": 30000, "actual": 33000 },
 *         "weight": { "budget": 15000, "actual": 14500 },
 *         "ad_hoc": { "budget": 0, "actual": 5000 },
 *         "rbs": { "budget": -5000, "actual": -3000 },
 *         "pickup": { "budget": 10000, "actual": 11000 },
 *         "other": { "budget": 70000, "actual": 69500 }
 *       }
 *     },
 *     ...
 *   ]
 * }
 *
 * Output: JSON with full variance decomposition
 */

const fs = require('fs');

const INPUT_PATH = process.argv[2] || 'variance_input.json';

(async () => {
    try {
        const input = JSON.parse(fs.readFileSync(INPUT_PATH, 'utf-8'));
        const facilities = input.facilities;

        // === TOTALS ===
        const totalBudgetCost = facilities.reduce((s, f) => s + f.budget_cost, 0);
        const totalActualCost = facilities.reduce((s, f) => s + f.actual_cost, 0);
        const totalBudgetVol = facilities.reduce((s, f) => s + f.budget_vol, 0);
        const totalActualVol = facilities.reduce((s, f) => s + f.actual_vol, 0);
        const totalVariance = totalActualCost - totalBudgetCost;

        const budgetCPP = totalBudgetVol > 0 ? totalBudgetCost / totalBudgetVol : 0;
        const actualCPP = totalActualVol > 0 ? totalActualCost / totalActualVol : 0;

        // === VOLUME VARIANCE ===
        // (Actual vol - Budget vol) × Budget CPP
        const volumeVariance = (totalActualVol - totalBudgetVol) * budgetCPP;

        // === SITE MIX VARIANCE ===
        // Actual vol × (Weighted avg budget CPP at actual mix - Overall budget CPP)
        // Weighted avg budget CPP at actual mix = sum(actual_vol_i × budget_cpp_i) / total_actual_vol
        let weightedBudgetCPP_atActualMix = 0;
        for (const f of facilities) {
            const facBudgetCPP = f.budget_vol > 0 ? f.budget_cost / f.budget_vol : 0;
            const actualMixWeight = totalActualVol > 0 ? f.actual_vol / totalActualVol : 0;
            weightedBudgetCPP_atActualMix += actualMixWeight * facBudgetCPP;
        }
        const mixVariance = totalActualVol * (weightedBudgetCPP_atActualMix - budgetCPP);

        // === RATE VARIANCE ===
        // Actual vol × (Actual CPP - Weighted avg budget CPP at actual mix)
        const rateVariance = totalActualVol * (actualCPP - weightedBudgetCPP_atActualMix);

        // === COMPONENT BREAKDOWN OF RATE VARIANCE ===
        const componentNames = ['stop_fee', 'b2c', 'weight', 'ad_hoc', 'rbs', 'pickup', 'other'];
        const componentVariances = {};

        for (const comp of componentNames) {
            let budgetTotal = 0;
            let actualTotal = 0;
            for (const f of facilities) {
                if (f.components && f.components[comp]) {
                    budgetTotal += f.components[comp].budget || 0;
                    actualTotal += f.components[comp].actual || 0;
                }
            }
            componentVariances[comp] = {
                budget: budgetTotal,
                actual: actualTotal,
                variance: actualTotal - budgetTotal,
            };
        }

        // === FACILITY-LEVEL DETAIL ===
        const facilityDetail = facilities.map(f => {
            const bCPP = f.budget_vol > 0 ? f.budget_cost / f.budget_vol : 0;
            const aCPP = f.actual_vol > 0 ? f.actual_cost / f.actual_vol : 0;
            const delta = f.actual_cost - f.budget_cost;
            const volDelta = f.actual_vol - f.budget_vol;
            const facVolumeVar = volDelta * bCPP;
            const facRateVar = f.actual_vol * (aCPP - bCPP);

            // Flag double whammy
            const doubleWhammy = aCPP > bCPP && f.actual_vol < f.budget_vol;

            return {
                name: f.name,
                budget_cost: f.budget_cost,
                actual_cost: f.actual_cost,
                delta: delta,
                delta_pct: f.budget_cost > 0 ? delta / f.budget_cost : 0,
                budget_vol: f.budget_vol,
                actual_vol: f.actual_vol,
                vol_delta: volDelta,
                budget_cpp: Math.round(bCPP * 100) / 100,
                actual_cpp: Math.round(aCPP * 100) / 100,
                cpp_delta: Math.round((aCPP - bCPP) * 100) / 100,
                volume_variance: Math.round(facVolumeVar),
                rate_variance: Math.round(facRateVar),
                double_whammy: doubleWhammy,
                pct_of_total_variance: totalVariance !== 0 ? Math.round(Math.abs(delta / totalVariance) * 1000) / 10 : 0,
            };
        }).sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta));

        // === VALIDATION ===
        const bridgeSum = volumeVariance + mixVariance + rateVariance;
        const residual = totalVariance - bridgeSum;
        const ties = Math.abs(residual) < Math.max(100, Math.abs(totalVariance) * 0.005);

        // === RED FLAGS ===
        const redFlags = [];

        // CPP increasing while volume flat/up
        if (actualCPP > budgetCPP && totalActualVol >= totalBudgetVol) {
            redFlags.push(`CPP increasing ($${actualCPP.toFixed(2)} vs $${budgetCPP.toFixed(2)} budget) despite volume at/above plan — rate problem`);
        }

        // Single facility >40% of variance
        if (facilityDetail.length > 0 && facilityDetail[0].pct_of_total_variance > 40) {
            redFlags.push(`${facilityDetail[0].name} drives ${facilityDetail[0].pct_of_total_variance}% of total variance — concentration risk`);
        }

        // Ad hoc > 10% of total variance
        if (componentVariances.ad_hoc && totalVariance !== 0) {
            const adHocPct = Math.abs(componentVariances.ad_hoc.variance / totalVariance);
            if (adHocPct > 0.10) {
                redFlags.push(`Ad hoc costs are ${(adHocPct * 100).toFixed(0)}% of total variance ($${componentVariances.ad_hoc.variance.toLocaleString()}) — investigate`);
            }
        }

        // Double whammies
        const dw = facilityDetail.filter(f => f.double_whammy);
        if (dw.length > 0) {
            redFlags.push(`Double whammy (CPP↑ + Vol↓) at: ${dw.map(f => f.name).join(', ')}`);
        }

        // Top 3 > 60%
        if (facilityDetail.length >= 3) {
            const top3pct = facilityDetail.slice(0, 3).reduce((s, f) => s + f.pct_of_total_variance, 0);
            if (top3pct > 60) {
                redFlags.push(`Top 3 facilities account for ${top3pct.toFixed(0)}% of total variance`);
            }
        }

        // === OUTPUT ===
        const output = {
            period: input.period,
            summary: {
                budget_cost: totalBudgetCost,
                actual_cost: totalActualCost,
                total_variance: totalVariance,
                variance_pct: totalBudgetCost > 0 ? totalVariance / totalBudgetCost : 0,
                budget_vol: totalBudgetVol,
                actual_vol: totalActualVol,
                budget_cpp: Math.round(budgetCPP * 100) / 100,
                actual_cpp: Math.round(actualCPP * 100) / 100,
                cpp_delta: Math.round((actualCPP - budgetCPP) * 100) / 100,
            },
            variance_bridge: {
                volume: Math.round(volumeVariance),
                site_mix: Math.round(mixVariance),
                rate: Math.round(rateVariance),
                residual: Math.round(residual),
                validation: ties ? 'TIES' : `GAP: $${residual.toLocaleString()}`,
            },
            component_detail: componentVariances,
            top_10_facilities: facilityDetail.slice(0, 10),
            all_facilities: facilityDetail,
            red_flags: redFlags,
        };

        console.log(JSON.stringify(output, null, 2));

    } catch (err) {
        console.error(JSON.stringify({ error: err.message }));
        process.exit(1);
    }
})();
