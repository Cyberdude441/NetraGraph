export interface CircularLoopHop {
  hopIndex: number;
  fromEntityId: string;
  fromEntityName: string;
  toEntityId: string;
  toEntityName: string;
  amountINR: number;
  timestamp: string;
  channel: string;
}

export interface CircularLoopPattern {
  loopId: string;
  originEntityId: string;
  originEntityName: string;
  totalTransferredINR: number;
  hopCount: number;
  hops: CircularLoopHop[];
  confidence: number;
}

export interface CommunicationBurstPoint {
  date: string;
  callCount: number;
  isSpike: boolean;
  baseline: number;
}

export interface CommunicationBurstPattern {
  entityId: string;
  entityName: string;
  baselineDailyAvg: number;
  peakDailyCount: number;
  surgePercentage: number;
  targetEntities: string[];
  history: CommunicationBurstPoint[];
}

export interface BurnerDevicePattern {
  imei: string;
  deviceName: string;
  primarySuspectId: string;
  primarySuspectName: string;
  associatedSimCards: {
    imsi: string;
    phoneNumber: string;
    carrier: string;
    firstSeen: string;
    lastSeen: string;
    isCurrentActive: boolean;
  }[];
  concurrentIdentitiesCount: number;
}

export interface NetworkGrowthPattern {
  communityId: number;
  communityName: string;
  priorSize: number;
  currentSize: number;
  netNewConnections: number;
  growthRatePercentage: number;
  timeWindowDays: number;
  newBridgeNodes: { id: string; name: string }[];
}

export interface LocationCoLocationPattern {
  towerId: string;
  cellSector: string;
  locationName: string;
  latitude: number;
  longitude: number;
  timeWindow: {
    start: string;
    end: string;
  };
  coLocatedEntities: {
    entityId: string;
    name: string;
    role: string;
    riskScore: number;
    phoneOrImei: string;
  }[];
  coLocationConfidence: number;
}
