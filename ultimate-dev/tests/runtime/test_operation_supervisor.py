from runtime.core.operation_supervisor import OperationSupervisor


class Store:
    def __init__(self):
        self.operations = [{
            "operation_id": "op-1",
            "task_id": "task-1",
            "status": "running",
            "worker_id": "worker-1",
            "lease_expires_at_epoch": 99.0,
        }]
        self.renewals = []
        self.recovered = 0

    def list_operations(self, task_id):
        return [item for item in self.operations if item["task_id"] == task_id]

    def renew_operation_lease(self, task_id, operation_id, worker_id, lease_seconds):
        self.renewals.append((operation_id, worker_id, lease_seconds))
        self.operations[0]["lease_expires_at_epoch"] = 200.0

    def recover_stale_operations(self, task_id):
        self.recovered += 1
        return 1


def test_supervisor_renews_owned_leases_and_reaps_stale_work():
    store = Store()
    supervisor = OperationSupervisor(store, "worker-1", lease_seconds=10, clock=lambda: 100.0)
    report = supervisor.tick("task-1")
    assert report == {"renewed": 1, "stale": 1, "recovered": 1}
    assert store.renewals == [("op-1", "worker-1", 10.0)]
    assert store.recovered == 1
