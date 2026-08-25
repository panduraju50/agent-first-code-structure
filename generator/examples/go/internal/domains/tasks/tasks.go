// unit: tasks (domains)
// capabilities: create_task, list_tasks
// effects: store
// uses: ids, validation
// GENERATED SKELETON — edges are declared in the project spec.

package tasks

import (
	"example.com/taskly/internal/core/ids"
	"example.com/taskly/internal/core/validation"
)

var _ = ids.EncodeId
var _ = validation.ValidateEmail

func CreateTask() error {
	return nil // TODO
}

func ListTasks() error {
	return nil // TODO
}

