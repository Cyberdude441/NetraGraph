export interface RiskFactorContribution {
  factorName: string;
  pointsAdded: number;
  description: string;
}

export interface DynamicRiskAssessment {
  entityId: string;
  entityName: string;
  baselineRiskScore: number;
  recalibratedRiskScore: number;
  delta: number;
  threatTier: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  contributions: RiskFactorContribution[];
  disclaimer: string;
}

/**
 * Dynamically compute risk score adjustments based on active detected anomalies
 */
export function calculateDynamicRiskImpact(
  baselineScore: number,
  entityId: string,
  entityName: string,
  activeAnomalyCategories: string[]
): DynamicRiskAssessment {
  const contributions: RiskFactorContribution[] = [];
  let addedPoints = 0;

  if (activeAnomalyCategories.includes("CIRCULAR_FINANCIAL_LOOP")) {
    const pts = 18;
    addedPoints += pts;
    contributions.push({
      factorName: "Circular Layering & Money Laundering Loop",
      pointsAdded: pts,
      description: "Entity identified as originator or terminal mule in automated fund cycling loop.",
    });
  }

  if (activeAnomalyCategories.includes("DEVICE_HOPPING")) {
    const pts = 15;
    addedPoints += pts;
    contributions.push({
      factorName: "Burner Hardware / IMEI Hopping Behavior",
      pointsAdded: pts,
      description: "Linked to multiple recycled IMSI SIM cards within short surveillance interval.",
    });
  }

  if (activeAnomalyCategories.includes("COMMUNICATION_BURST")) {
    const pts = 12;
    addedPoints += pts;
    contributions.push({
      factorName: "High-Volume Telephony Burst (+350%)",
      pointsAdded: pts,
      description: "Sudden spike in high-frequency coordination calls prior to cyber incident.",
    });
  }

  if (activeAnomalyCategories.includes("GEOSPATIAL_CO_LOCATION")) {
    const pts = 10;
    addedPoints += pts;
    contributions.push({
      factorName: "Cell-Tower Physical Co-Location",
      pointsAdded: pts,
      description: "Co-located with 3+ flagged syndicate operatives in suspicious operational zone.",
    });
  }

  if (activeAnomalyCategories.includes("NETWORK_EXPANSION_SURGE")) {
    const pts = 8;
    addedPoints += pts;
    contributions.push({
      factorName: "Inter-Cluster Syndicate Bridge Formation",
      pointsAdded: pts,
      description: "Formed rapid cross-community relationships with external cyber cell.",
    });
  }

  const finalScore = Math.min(100, Math.max(0, baselineScore + addedPoints));

  let tier: DynamicRiskAssessment["threatTier"] = "LOW";
  if (finalScore >= 85) tier = "CRITICAL";
  else if (finalScore >= 70) tier = "HIGH";
  else if (finalScore >= 50) tier = "MEDIUM";

  return {
    entityId,
    entityName,
    baselineRiskScore: baselineScore,
    recalibratedRiskScore: finalScore,
    delta: finalScore - baselineScore,
    threatTier: tier,
    contributions,
    disclaimer:
      "Dynamic analytical risk indicator based on synthetic telemetry. Reflects algorithmic graph signals, not a judicial conviction.",
  };
}
