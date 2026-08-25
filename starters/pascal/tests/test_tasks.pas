{ test_tasks.pas — the required test for the Tasks domain. Note it never
  imports Users: assignment is exercised with a plain string id, proving
  Tasks does not need the Users domain to do its job. }
program TestTasks;

{$mode objfpc}{$H+}

uses
  Core, Tasks;

var
  failures: Integer = 0;

procedure Check(Cond: Boolean; const Msg: string);
begin
  if not Cond then
  begin
    WriteLn('FAIL: ', Msg);
    Inc(failures);
  end
  else
    WriteLn('PASS: ', Msg);
end;

var
  Store: TTaskStore;
  T: TTask;
  Err: string;
  All: TTaskArray;

begin
  Store.NextId := 0;

  Check(CreateTask(Store, 'Write README', T, Err) = True,
    'CreateTask succeeds for a non-empty title');
  Check(T.Id <> '', 'created task gets a non-empty id (from Core.Base62Encode)');
  Check(T.Status = tsOpen, 'a new task starts as tsOpen');

  Check(CreateTask(Store, '   ', T, Err) = False,
    'CreateTask rejects a blank title (via Core.IsNonEmptyTitle)');
  Check(Length(Store.Items) = 1, 'rejected creates do not grow the store');

  Check(AssignTask(Store, Store.Items[0].Id, 'u_1', Err) = True,
    'AssignTask succeeds for an existing task id, given a plain user-id string');
  Check(AssignTask(Store, 'no-such-task', 'u_1', Err) = False,
    'AssignTask reports a missing task id');

  All := ListTasks(Store);
  Check(Length(All) = 1, 'ListTasks reflects the store contents');
  Check(All[0].AssigneeId = 'u_1', 'the assignment is visible via ListTasks');
  Check(All[0].Status = tsAssigned, 'status flips to tsAssigned on assignment');

  if failures > 0 then
  begin
    WriteLn(failures, ' failure(s)');
    Halt(1);
  end;
  WriteLn('all tasks tests passed');
end.
