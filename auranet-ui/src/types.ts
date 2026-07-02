/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

export type ActiveView = 'main' | 'stress' | 'statistics' | 'attack' | 'workload';

export interface SystemNode {
  id: string;
  label: string;
  type: 'central' | 'sensor' | 'gateway' | 'compute';
  status: 'active' | 'warning' | 'offline';
  latency: number; // in ms
  region: string;
  ip: string;
  cpu: number; // percentage
  memory: number; // percentage
  connections: string[]; // ids of connected nodes
}

export interface MetricData {
  option1: number; // e.g. 538
  option2: number; // e.g. 485
  option3: number; // e.g. 45
  option1Percent: number; // e.g. 75
  option2Percent: number; // e.g. 40
}

export interface CommitLog {
  id: string;
  author: string;
  avatar: string;
  timeAgo: string;
  message: string;
  nodeId?: string;
  category: 'logic' | 'security' | 'infra' | 'performance';
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
}
