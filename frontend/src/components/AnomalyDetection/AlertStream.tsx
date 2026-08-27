import React from "react";
import {
  Flame,
  ShieldAlert,
  Clock,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  CreditCard,
  PhoneCall,
  Cpu,
  TrendingUp,
  MapPin,
  ArrowRight,
  User,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { AnomalyAlert } from "@/utils/anomalyDetection";

interface AlertStreamProps {
  alerts: AnomalyAlert[];
  selectedAlertId: string | null;
  onSelectAlert: (id: string) => void;
}

const CATEGORY_ICONS: Record<string, React.ElementType> = {
  CIRCULAR_FINANCIAL_LOOP: CreditCard,
  DEVICE_HOPPING: Cpu,
  COMMUNICATION_BURST: PhoneCall,
  NETWORK_EXPANSION_SURGE: TrendingUp,
  GEOSPATIAL_CO_LOCATION: MapPin,
};

export function AlertStream({
  alerts,
  selectedAlertId,
  onSelectAlert,
}: AlertStreamProps) {
  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden select-none bg-white font-sans">
      {/* Top Header */}
      <div className="border-b border-[#E2E8F0] bg-[#F8FAFC] px-4 py-2.5 flex items-center justify-between text-xs">
        <div className="flex items-center gap-2">
          <span className="text-[#64748B] font-semibold">
            Urgent Alerts Queue:
          </span>
          <span className="font-bold text-[#064E3B]">{alerts.length} Flagged Anomalies</span>
        </div>

        <span className="text-xs text-[#64748B]">
          Sorted by severity
        </span>
      </div>

      {/* Alert Cards Stream */}
      <div className="flex-1 overflow-y-auto p-3.5 space-y-3 bg-[#F8FAFC]">
        {alerts.length === 0 ? (
          <div className="rounded-md border border-dashed border-[#E2E8F0] bg-white p-8 text-center text-[#64748B] text-xs">
            No anomaly patterns match the active filter criteria.
          </div>
        ) : (
          alerts.map((alert) => {
            const isSelected = selectedAlertId === alert.id;
            const Icon = CATEGORY_ICONS[alert.category] || ShieldAlert;
            const isCrit = alert.severity === "CRITICAL";
            const isHigh = alert.severity === "HIGH";

            return (
              <div
                key={alert.id}
                onClick={() => onSelectAlert(alert.id)}
                className={cn(
                  "rounded-md border p-4 transition-all cursor-pointer space-y-3 relative shadow-xs bg-white",
                  isSelected
                    ? "border-[#16A34A] ring-2 ring-[#16A34A]/20"
                    : "border-[#E2E8F0] hover:border-[#94A3B8]"
                )}
              >
                {/* Header Line */}
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-2.5 min-w-0">
                    <span
                      className={cn(
                        "flex size-8 shrink-0 items-center justify-center rounded-md border shadow-xs mt-0.5",
                        isCrit
                          ? "border-red-200 bg-red-50 text-[#DC2626]"
                          : isHigh
                          ? "border-orange-200 bg-orange-50 text-[#EA580C]"
                          : "border-amber-200 bg-amber-50 text-[#F59E0B]"
                      )}
                    >
                      <Icon className="size-4" />
                    </span>

                    <div className="min-w-0">
                      <h4 className="font-bold text-[#0F172A] text-sm truncate">
                        {alert.title}
                      </h4>
                      <p className="text-xs text-[#64748B] truncate mt-0.5">
                        Alert Ref: <strong className="font-mono text-[#064E3B]">{alert.id}</strong> · Target: <strong className="text-[#0F172A]">{alert.primaryEntityName}</strong>
                      </p>
                    </div>
                  </div>

                  {/* Severity Badge */}
                  <span
                    className={cn(
                      "shrink-0 flex items-center gap-1 rounded-md px-2.5 py-0.5 text-xs font-bold",
                      isCrit
                        ? "bg-red-50 text-[#DC2626] border border-red-200"
                        : isHigh
                        ? "bg-orange-50 text-[#EA580C] border border-orange-200"
                        : "bg-amber-50 text-[#F59E0B] border border-amber-200"
                    )}
                  >
                    {isCrit && <Flame className="size-3 text-[#DC2626]" />}
                    {alert.severity === "CRITICAL" ? "Critical Alert" : alert.severity === "HIGH" ? "High Risk" : "Medium Watch"}
                  </span>
                </div>

                {/* Evidence & Confidence Section */}
                <div className="rounded-md bg-[#F8FAFC] p-3 border border-[#E2E8F0] text-xs space-y-1.5">
                  <div className="flex items-center justify-between text-xs font-bold text-[#064E3B]">
                    <span>Observation</span>
                    <span className="font-semibold text-xs text-[#16A34A]">Confidence: {alert.confidenceScore}%</span>
                  </div>
                  <p className="text-[#CBD5E1] leading-normal">{alert.observation}</p>
                  
                  {/* Evidence check bullets */}
                  <div className="pt-1.5 space-y-1 text-xs text-[#CBD5E1] border-t border-[#E2E8F0]">
                    <div className="flex items-center gap-1.5 text-xs font-semibold text-[#0F172A]">
                      <CheckCircle2 className="size-3.5 text-[#16A34A]" />
                      <span>{alert.analysis || "Pattern corroborated by multi-hop graph analysis"}</span>
                    </div>
                  </div>
                </div>

                {/* Recommended Action */}
                <div className="rounded-md bg-emerald-50/60 p-2.5 border border-emerald-200/80 text-xs">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-[#064E3B] block">Recommended Action:</span>
                  <p className="text-xs text-[#064E3B] font-medium mt-0.5">{alert.recommendedAction || "Review transaction chain and initiate Section 91 CrPC notice"}</p>
                </div>

                {/* Related entities flow */}
                {alert.relatedEntities && alert.relatedEntities.length > 0 && (
                  <div className="pt-2 border-t border-[#E2E8F0] text-xs">
                    <span className="text-xs text-[#64748B] font-semibold block mb-1">Related Entities:</span>
                    <div className="flex flex-wrap items-center gap-1.5 font-medium text-[#064E3B]">
                      {alert.relatedEntities.map((ent, idx) => (
                        <React.Fragment key={idx}>
                          <span className="rounded bg-[#F1F5F9] px-2 py-0.5 border border-[#E2E8F0] text-xs">
                            {ent}
                          </span>
                          {idx < alert.relatedEntities.length - 1 && (
                            <ArrowRight className="size-3 text-[#94A3B8]" />
                          )}
                        </React.Fragment>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
