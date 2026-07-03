/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

export type ActiveView = 'main' | 'stress' | 'statistics' | 'attack' | 'workload';

export interface SystemAlert {
  id: string;
  title: string;
  message: string;
  type: 'critical' | 'warning' | 'success';
  timestamp: Date;
}

export interface SystemNode {
  id: string;
  label: string;
  type: 'central' | 'sensor' | 'gateway' | 'compute';
  status: 'active' | 'warning' | 'offline' | 'recovered';
  latency: number; 
  region: string;
  ip: string;
  cpu: number; 
  memory: number; 
  connections: string[]; 
}

export interface K8sNode {
  id: string;
  name: string;
  status: 'active' | 'warning' | 'offline';
  ip: string;
  cpu: number;
  memory: number;
}

export interface AuraNode {
  id: string;
  name: string;
  status: 'active' | 'warning' | 'offline';
  ip: string;
  role: 'controller' | 'engine';
  cpu: number;
  memory: number;
}

export interface MetricData {
  option1: number; 
  option2: number; 
  option3: number; 
  option1Percent: number; 
  option2Percent: number; 
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



