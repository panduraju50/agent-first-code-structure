// unit: app (app)
// capabilities: run
// effects: store, net
// uses: users, tasks, notifier
// GENERATED SKELETON — edges are declared in the project spec.

package main

import (
	"example.com/taskly/internal/domains/users"
	"example.com/taskly/internal/domains/tasks"
	"example.com/taskly/internal/domains/notifier"
)

var _ = users.CreateUser
var _ = tasks.CreateTask
var _ = notifier.Notify

func main() {
	// composition root: wire the domains here
}

