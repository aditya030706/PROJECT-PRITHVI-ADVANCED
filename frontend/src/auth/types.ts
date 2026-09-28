export type UserRole =
    | "FIELD_INSPECTOR"
    | "MINE_SUPERVISOR"
    | "MINE_MANAGER"
    | "CORPORATE_MANAGEMENT";

export type UserSession = {
    user_id: string;
    name: string;
    role: UserRole;

    mine_id?: string;
    region?: string;
    subsidiary?: string;
};