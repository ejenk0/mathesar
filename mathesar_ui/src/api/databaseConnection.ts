import type { Database } from '@mathesar/AppTypes';
import { patchAPI, postAPI } from './utils/requestUtils';

export interface NewConnection {
  name: string;
  db_name: string;
  username: string;
  host: string;
  port: string;
  password: string;
}

export type ConnectionUpdates = Partial<Omit<NewConnection, 'name'>>;

function add(connectionDetails: NewConnection) {
  return postAPI<Database>('/api/db/v0/databases/', connectionDetails);
}

function update(databaseId: number, updates: ConnectionUpdates) {
  return patchAPI<Database>(`/api/db/v0/databases/${databaseId}/`, updates);
}

export default {
  add,
  update,
};