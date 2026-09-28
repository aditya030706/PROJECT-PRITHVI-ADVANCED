import { apiGet } from "./client";

export type MineInspectionSchedule = {
    schedule_instance_id: string;
    mine_id: string;
    schedule_id: string;
    last_completed_at: string | null;
    next_due_at: string | null;
    status: string;
    generated_at: string;

    active: number;

    schedule_name: string;
    template_id: string;
    obligation_id: string;

    frequency_type: string;
    interval_value: number | null;
    interval_unit: string | null;

    trigger_type: string;
    validation_status: string;

    name?: string;
    template_name?: string;
    inspection_family?: string;
    frequency_label?: string;
    responsible_role?: string;
    regulation_reference?: string;
};

export type MineScheduleResponse = {
    mine_id: string;
    count: number;
    schedules: MineInspectionSchedule[];
};

export async function getMineSchedule(
    mineId: string
): Promise<MineScheduleResponse> {
    return apiGet<MineScheduleResponse>(
        `/api/mines/${mineId}/schedule`
    );
}