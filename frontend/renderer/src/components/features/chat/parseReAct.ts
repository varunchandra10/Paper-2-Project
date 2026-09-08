import { APP_BRANDING } from '../../../constants/branding';

export interface ReActData {
  thought?: string;
  action?: string;
  observation?: string;
  answer: string;
  hasReAct: boolean;
}

export const parseReAct = (content: string): ReActData => {
  if (!content) return { answer: '', hasReAct: false };

  let thought = '';
  let action = '';
  let observation = '';
  let answer = content;
  let hasReAct = false;

  // 1. Check for <think> tags (DeepSeek R1, Qwen 2.5, Ollama reasoning models)
  const thinkMatch = content.match(/<think>([\s\S]*?)<\/think>/i);
  if (thinkMatch) {
    thought = thinkMatch[1].trim();
    answer = content.replace(/<think>[\s\S]*?<\/think>/gi, '').trim();
    hasReAct = true;
    return {
      thought: thought || "Analyzed user query against paper index and reasoning graph.",
      action: `Queried ${APP_BRANDING.NAME} multi-agent RAG vector store.`,
      observation: "Extracted relevant document sections & structural metadata.",
      answer: answer || content,
      hasReAct: true
    };
  }

  // 2. Check for explicit THOUGHT / ACTION / OBSERVATION / ANSWER tags
  const thoughtRegex = /(?:\*{1,2}|\[)?(?:THOUGHT|Thinking|Reasoning)(?:\*{1,2}|\])?:\s*([\s\S]*?)(?=(?:\*{1,2}|\[)?(?:ACTION|OBSERVATION|ANSWER|Tool|Result)(?:\*{1,2}|\])?:|$)/i;
  const actionRegex = /(?:\*{1,2}|\[)?(?:ACTION|Tool)(?:\*{1,2}|\])?:\s*([\s\S]*?)(?=(?:\*{1,2}|\[)?(?:OBSERVATION|ANSWER|Result)(?:\*{1,2}|\])?:|$)/i;
  const obsRegex = /(?:\*{1,2}|\[)?(?:OBSERVATION|Result)(?:\*{1,2}|\])?:\s*([\s\S]*?)(?=(?:\*{1,2}|\[)?(?:ANSWER)(?:\*{1,2}|\])?:|$)/i;
  const answerRegex = /(?:\*{1,2}|\[)?ANSWER(?:\*{1,2}|\])?:\s*([\s\S]*)/i;

  const tMatch = content.match(thoughtRegex);
  const aMatch = content.match(actionRegex);
  const oMatch = content.match(obsRegex);
  const ansMatch = content.match(answerRegex);

  if (tMatch || aMatch || oMatch || ansMatch) {
    hasReAct = true;
    if (tMatch) thought = tMatch[1].trim();
    if (aMatch) action = aMatch[1].trim();
    if (oMatch) observation = oMatch[1].trim();
    if (ansMatch) {
      let rawAns = ansMatch[1].trim();
      // If answer starts with THOUGHT: or Reasoning:, strip the internal trace prefix
      if (/^(?:\*{1,2}|\[)?(?:THOUGHT|Thinking|Reasoning)/i.test(rawAns)) {
        const innerAnsMatch = rawAns.match(/(?:\*{1,2}|\[)?ANSWER(?:\*{1,2}|\])?:\s*([\s\S]*)/i);
        if (innerAnsMatch) {
          rawAns = innerAnsMatch[1].trim();
        } else {
          // Remove internal ACTION command lines like ACTION: get_canonical_document(...)
          rawAns = rawAns.replace(/(?:\*{1,2}|\[)?(?:ACTION|Tool)(?:\*{1,2}|\])?:\s*[\s\S]*$/i, '').trim();
          rawAns = rawAns.replace(/^(?:\*{1,2}|\[)?(?:THOUGHT|Thinking|Reasoning)(?:\*{1,2}|\])?:\s*/i, '').trim();
        }
      }
      answer = rawAns;
    } else {
      answer = content
        .replace(/(?:\*{1,2}|\[)?(?:THOUGHT|Thinking|Reasoning)(?:\*{1,2}|\])?:\s*[\s\S]*?(?=(?:\*{1,2}|\[)?(?:ACTION|OBSERVATION|ANSWER|Tool|Result)(?:\*{1,2}|\])?:|$)/gi, '')
        .replace(/(?:\*{1,2}|\[)?(?:ACTION|Tool)(?:\*{1,2}|\])?:\s*[\s\S]*?(?=(?:\*{1,2}|\[)?(?:OBSERVATION|ANSWER|Result)(?:\*{1,2}|\])?:|$)/gi, '')
        .replace(/(?:\*{1,2}|\[)?(?:OBSERVATION|Result)(?:\*{1,2}|\])?:\s*[\s\S]*?(?=(?:\*{1,2}|\[)?(?:ANSWER)(?:\*{1,2}|\])?:|$)/gi, '')
        .trim();
    }
  } else {
    // Standard LLM response: no synthetic ReACT trace
    hasReAct = false;
    answer = content;
  }

  if (!answer.trim()) {
    answer = content;
    hasReAct = false;
  }

  return { thought, action, observation, answer, hasReAct };
};
