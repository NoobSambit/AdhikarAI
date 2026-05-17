"use client";

import { openDB, DBSchema } from "idb";
import { LanguageCode, SchemeCardView } from "@/lib/api";

export interface GuestProfile {
  id: string;
  language_code: LanguageCode;
  high_contrast_enabled: boolean;
  font_size: "default" | "large" | "extra_large";
  created_at: string;
  updated_at: string;
}

export interface ConversationRecord {
  id: string;
  language_code: LanguageCode;
  turns: Array<{ role: "user" | "assistant"; content: string; created_at: string }>;
  matched_scheme_count: number;
  updated_at: string;
}

export interface LocalChecklist {
  id: string;
  scheme_id: string;
  document_name: string;
  status: "not_gathered" | "gathered" | "verified" | "rejected";
  updated_at: string;
}

export interface SyncQueueItem {
  idempotency_key: string;
  action_type: string;
  payload: Record<string, unknown>;
  created_at: string;
  retry_count: number;
  next_attempt_at: string;
}

interface AdhikarDb extends DBSchema {
  cached_schemes: { key: string; value: SchemeCardView };
  guest_profile: { key: string; value: GuestProfile };
  conversation_history: { key: string; value: ConversationRecord };
  local_checklist_state: { key: string; value: LocalChecklist };
  sync_queue: { key: string; value: SyncQueueItem };
}

const DB_NAME = "adhikarai_phase4";

export async function db() {
  return openDB<AdhikarDb>(DB_NAME, 1, {
    upgrade(database) {
      database.createObjectStore("cached_schemes", { keyPath: "scheme_id" });
      database.createObjectStore("guest_profile", { keyPath: "id" });
      database.createObjectStore("conversation_history", { keyPath: "id" });
      database.createObjectStore("local_checklist_state", { keyPath: "id" });
      database.createObjectStore("sync_queue", { keyPath: "idempotency_key" });
    }
  });
}

export async function getOrCreateGuestProfile(languageCode: LanguageCode): Promise<GuestProfile> {
  const database = await db();
  const existing = (await database.getAll("guest_profile"))[0];
  if (existing) return existing;
  const now = new Date().toISOString();
  const profile: GuestProfile = {
    id: crypto.randomUUID(),
    language_code: languageCode,
    high_contrast_enabled: false,
    font_size: "default",
    created_at: now,
    updated_at: now
  };
  await database.put("guest_profile", profile);
  return profile;
}

export async function saveGuestProfile(profile: GuestProfile) {
  await (await db()).put("guest_profile", { ...profile, updated_at: new Date().toISOString() });
}

export async function appendConversationTurn(id: string, languageCode: LanguageCode, role: "user" | "assistant", content: string, matchedSchemeCount = 0) {
  const database = await db();
  const existing = await database.get("conversation_history", id);
  const now = new Date().toISOString();
  await database.put("conversation_history", {
    id,
    language_code: languageCode,
    turns: [...(existing?.turns ?? []), { role, content, created_at: now }],
    matched_scheme_count: Math.max(existing?.matched_scheme_count ?? 0, matchedSchemeCount),
    updated_at: now
  });
}

export async function getHistory() {
  return (await (await db()).getAll("conversation_history")).sort((a, b) => b.updated_at.localeCompare(a.updated_at));
}

export async function cacheSchemes(schemes: SchemeCardView[]) {
  const database = await db();
  await Promise.all(schemes.map((scheme) => database.put("cached_schemes", scheme)));
}

export async function getCachedSchemes() {
  return (await db()).getAll("cached_schemes");
}

export async function saveLocalChecklist(item: LocalChecklist) {
  await (await db()).put("local_checklist_state", { ...item, updated_at: new Date().toISOString() });
}

export async function getLocalChecklist() {
  return (await db()).getAll("local_checklist_state");
}

export function nextAttempt(retryCount: number) {
  const seconds = Math.min(300, 2 ** retryCount * 5);
  return new Date(Date.now() + seconds * 1000).toISOString();
}

export async function enqueueSync(actionType: string, payload: Record<string, unknown>) {
  const item: SyncQueueItem = {
    idempotency_key: crypto.randomUUID(),
    action_type: actionType,
    payload,
    created_at: new Date().toISOString(),
    retry_count: 0,
    next_attempt_at: new Date().toISOString()
  };
  await (await db()).put("sync_queue", item);
  return item;
}

export async function getSyncQueue() {
  return (await db()).getAll("sync_queue");
}
