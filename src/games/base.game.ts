import { TextChannel, Message } from 'discord.js';

export interface GameDefinition {
  id: string;
  category: string;
  name: string;
  duration: number;
  mediaCount: number;
  voteType: string;
  voteEmojis: string[];
  voteLabels?: string[];
  hasCorrectAnswer: boolean;
  isDelayed?: boolean;
  delayDuration?: string;
  scoring: any;
  teamBonuses?: any;
  specialRole?: string;
  antiCheat?: string;
  requiresAI?: boolean;
}

export abstract class BaseGame {
  constructor(public def: GameDefinition) {}

  abstract startRound(channel: TextChannel): Promise<Message>;
  abstract endRound(messageId: string): Promise<void>;
  
  protected async tallyVotes(roundId: string) {
    // Logic to tally from Redis
  }
}
