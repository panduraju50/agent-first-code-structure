{ app.pas — the composition root.

  Design D rule 2's exception: this is the ONLY file allowed to import both
  domains at once. It wires Users and Tasks together (by passing a
  Users-minted id into Tasks.AssignTask) and runs a tiny end-to-end scenario. }
program App;

{$mode objfpc}{$H+}

uses SysUtils, Core, Users, Tasks;

var
  UserStore: TUserStore;
  TaskStore: TTaskStore;
  Alice: TUser;
  T1: TTask;
  ErrMsg: string;
  AllTasks: TTaskArray;
  i: Integer;

begin
  UserStore.NextId := 0;
  TaskStore.NextId := 0;

  if not CreateUser(UserStore, 'Alice', 'alice@example.com', Alice, ErrMsg) then
  begin
    WriteLn('failed to create user: ', ErrMsg);
    Halt(1);
  end;
  WriteLn('created user ', Alice.Id, ' (', Alice.Name, ' <', Alice.Email, '>)');

  if not CreateTask(TaskStore, 'Write Design D README', T1, ErrMsg) then
  begin
    WriteLn('failed to create task: ', ErrMsg);
    Halt(1);
  end;
  WriteLn('created task ', T1.Id, ' "', T1.Title, '"');

  { The composition root is the glue: it hands Tasks a plain user id string.
    Tasks never imported Users to make this possible. }
  if not AssignTask(TaskStore, T1.Id, Alice.Id, ErrMsg) then
  begin
    WriteLn('failed to assign task: ', ErrMsg);
    Halt(1);
  end;
  WriteLn('assigned task ', T1.Id, ' to ', Alice.Id);

  AllTasks := ListTasks(TaskStore);
  WriteLn('tasks (', Length(AllTasks), '):');
  for i := 0 to High(AllTasks) do
    WriteLn('  ', AllTasks[i].Id, ' [status=', Ord(AllTasks[i].Status), '] "',
      AllTasks[i].Title, '" assignee=', AllTasks[i].AssigneeId);
end.
