import { openDB, IDBPDatabase } from 'idb'
import type { OfflineInspection } from '@/types'

const DB_NAME = 'coalmine-offline'
const DB_VERSION = 1
const INSPECTION_STORE = 'inspections'
const PHOTO_STORE = 'photos'

let db: IDBPDatabase | null = null

export async function getDB(): Promise<IDBPDatabase> {
  if (db) return db
  db = await openDB(DB_NAME, DB_VERSION, {
    upgrade(database) {
      if (!database.objectStoreNames.contains(INSPECTION_STORE)) {
        const store = database.createObjectStore(INSPECTION_STORE, { keyPath: 'clientId' })
        store.createIndex('syncStatus', 'syncStatus')
        store.createIndex('mineId', 'mineId')
      }
      if (!database.objectStoreNames.contains(PHOTO_STORE)) {
        database.createObjectStore(PHOTO_STORE, { keyPath: 'id' })
      }
    },
  })
  return db
}

// ─── Inspection CRUD ───────────────────────────────────
export async function saveInspection(inspection: OfflineInspection): Promise<void> {
  const database = await getDB()
  await database.put(INSPECTION_STORE, inspection)
}

export async function getInspection(clientId: string): Promise<OfflineInspection | undefined> {
  const database = await getDB()
  return database.get(INSPECTION_STORE, clientId)
}

export async function getPendingInspections(): Promise<OfflineInspection[]> {
  const database = await getDB()
  const all = await database.getAll(INSPECTION_STORE)
  return all.filter((i) => i.syncStatus === 'pending' || i.syncStatus === 'failed')
}

export async function getAllInspections(): Promise<OfflineInspection[]> {
  const database = await getDB()
  return database.getAll(INSPECTION_STORE)
}

export async function deleteInspection(clientId: string): Promise<void> {
  const database = await getDB()
  await database.delete(INSPECTION_STORE, clientId)
}

export async function updateSyncStatus(
  clientId: string,
  status: 'pending' | 'syncing' | 'synced' | 'failed' | 'conflict'
): Promise<void> {
  const database = await getDB()
  const inspection = await database.get(INSPECTION_STORE, clientId)
  if (inspection) {
    inspection.syncStatus = status
    await database.put(INSPECTION_STORE, inspection)
  }
}

// ─── Photo storage ─────────────────────────────────────
export async function savePhoto(id: string, blob: Blob): Promise<void> {
  const database = await getDB()
  await database.put(PHOTO_STORE, { id, blob, savedAt: new Date().toISOString() })
}

export async function getPhoto(id: string): Promise<Blob | null> {
  const database = await getDB()
  const record = await database.get(PHOTO_STORE, id)
  return record?.blob ?? null
}

// ─── Pending count ─────────────────────────────────────
export async function getPendingCount(): Promise<number> {
  const pending = await getPendingInspections()
  return pending.length
}
