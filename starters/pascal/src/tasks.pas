{ tasks.pas — the Tasks domain.

  Design D rule 2, mirrored from users.pas: `uses Core;` only. Assignment
  is the one place a naive design would reach for Users (to check the
  assignee exists, to embed a TUser, whatever) — instead AssigneeId is an
  opaque string the composition root fills in with a Users-minted id. Tasks
  never imports Users to make that work. }
unit Tasks;

{$mode objfpc}{$H+}

interface

type
  TTaskStatus = (tsOpen, tsAssigned);

  TTask = record
    Id: string;
    Title: string;
    AssigneeId: string; { opaque reference to a Users id; Tasks does not know TUser }
    Status: TTaskStatus;
  end;

  TTaskArray = array of TTask;

  TTaskStore = record
    Items: TTaskArray;
    NextId: Int64;
  end;

function CreateTask(var Store: TTaskStore; const Title: string;
  out NewTask: TTask; out ErrMsg: string): Boolean;

function AssignTask(var Store: TTaskStore; const TaskId, UserId: string;
  out ErrMsg: string): Boolean;

function ListTasks(const Store: TTaskStore): TTaskArray;

implementation

uses Core;

function CreateTask(var Store: TTaskStore; const Title: string;
  out NewTask: TTask; out ErrMsg: string): Boolean;
begin
  Result := False;
  NewTask.Id := '';
  NewTask.Title := '';
  NewTask.AssigneeId := '';
  NewTask.Status := tsOpen;
  ErrMsg := '';

  if not Core.IsNonEmptyTitle(Title) then
  begin
    ErrMsg := 'task title must not be empty';
    Exit;
  end;

  Inc(Store.NextId);
  NewTask.Id := 't_' + Core.Base62Encode(Store.NextId);
  NewTask.Title := Title;

  SetLength(Store.Items, Length(Store.Items) + 1);
  Store.Items[High(Store.Items)] := NewTask;
  Result := True;
end;

function AssignTask(var Store: TTaskStore; const TaskId, UserId: string;
  out ErrMsg: string): Boolean;
var
  i: Integer;
begin
  Result := False;
  ErrMsg := '';

  if not Core.IsNonEmptyTitle(UserId) then
  begin
    ErrMsg := 'assignee id must not be empty';
    Exit;
  end;

  for i := 0 to High(Store.Items) do
    if Store.Items[i].Id = TaskId then
    begin
      Store.Items[i].AssigneeId := UserId;
      Store.Items[i].Status := tsAssigned;
      Result := True;
      Exit;
    end;

  ErrMsg := 'task not found: ' + TaskId;
end;

function ListTasks(const Store: TTaskStore): TTaskArray;
begin
  Result := Store.Items;
end;

end.
