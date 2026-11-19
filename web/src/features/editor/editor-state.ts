import { type Draft, type DraftPath, writePath } from '@/features/editor/input-document'
import type { Rejection } from '@/shared/api/schemas/diagnostics'
import type { Interpretation } from '@/shared/api/schemas/records'

export type CheckState =
  | { status: 'idle' }
  | { status: 'checking' }
  | { status: 'interpreted'; text: string; interpretation: Interpretation }
  | { status: 'rejected'; text: string; rejection: Rejection }
  | { status: 'failed'; message: string }

export type SubmissionState =
  { status: 'idle' } | { status: 'submitting' } | { status: 'failed'; message: string }

export type SubmissionAttempt = {
  text: string
  key: string
}

export type EditorState = {
  draft: Draft
  revision: number
  timeLimit: string
  check: CheckState
  submission: SubmissionState
  attempt: SubmissionAttempt | null
}

export type EditorAction =
  | { type: 'field_changed'; path: DraftPath; value: unknown }
  | { type: 'draft_replaced'; draft: Draft }
  | { type: 'time_limit_changed'; value: string }
  | { type: 'check_started' }
  | { type: 'check_finished'; check: CheckState }
  | { type: 'submission_started'; attempt: SubmissionAttempt }
  | { type: 'submission_failed'; message: string }

export function initialEditorState(draft: Draft, defaultTimeLimit: number): EditorState {
  return {
    draft,
    revision: 0,
    timeLimit: String(defaultTimeLimit),
    check: { status: 'idle' },
    submission: { status: 'idle' },
    attempt: null,
  }
}

export function editorReducer(state: EditorState, action: EditorAction): EditorState {
  switch (action.type) {
    case 'field_changed':
      return { ...state, draft: writePath(state.draft, action.path, action.value) }
    case 'draft_replaced':
      return { ...state, draft: action.draft, revision: state.revision + 1 }
    case 'time_limit_changed':
      return { ...state, timeLimit: action.value }
    case 'check_started':
      return { ...state, check: { status: 'checking' }, submission: { status: 'idle' } }
    case 'check_finished':
      return { ...state, check: action.check }
    case 'submission_started':
      return { ...state, attempt: action.attempt, submission: { status: 'submitting' } }
    case 'submission_failed':
      return { ...state, submission: { status: 'failed', message: action.message } }
  }
}

export function parseTimeLimit(text: string, maxSeconds: number): number | null {
  const seconds = Number(text.trim())
  if (text.trim() === '' || !Number.isFinite(seconds)) return null
  return seconds > 0 && seconds <= maxSeconds ? seconds : null
}
