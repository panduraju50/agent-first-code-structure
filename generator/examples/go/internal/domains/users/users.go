// unit: users (domains)
// capabilities: create_user, get_user
// effects: store
// uses: ids, validation
// GENERATED SKELETON — edges are declared in the project spec.

package users

import (
	"example.com/taskly/internal/core/ids"
	"example.com/taskly/internal/core/validation"
)

var _ = ids.EncodeId
var _ = validation.ValidateEmail

func CreateUser() error {
	return nil // TODO
}

func GetUser() error {
	return nil // TODO
}

