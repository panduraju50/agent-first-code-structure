{ test_users.pas — the required test for the Users domain. Exercises
  CreateUser/GetUser and, implicitly, that Users is really delegating
  validation and id encoding to Core rather than re-implementing them. }
program TestUsers;

{$mode objfpc}{$H+}

uses
  Core, Users;

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
  Store: TUserStore;
  U, Found: TUser;
  Err: string;

begin
  Store.NextId := 0;

  Check(CreateUser(Store, 'Alice', 'alice@example.com', U, Err) = True,
    'CreateUser succeeds for a valid name and email');
  Check(U.Id <> '', 'created user gets a non-empty id (from Core.Base62Encode)');
  Check(Length(Store.Items) = 1, 'store grows by one after a successful create');

  Check(CreateUser(Store, '', 'bob@example.com', U, Err) = False,
    'CreateUser rejects an empty name (via Core.IsNonEmptyTitle)');
  Check(CreateUser(Store, 'Bob', 'not-an-email', U, Err) = False,
    'CreateUser rejects a malformed email (via Core.IsValidEmail)');
  Check(Length(Store.Items) = 1, 'rejected creates do not grow the store');

  Check(GetUser(Store, Store.Items[0].Id, Found) = True,
    'GetUser finds a user by its id');
  Check(Found.Name = 'Alice', 'GetUser returns the matching record');
  Check(GetUser(Store, 'does-not-exist', Found) = False,
    'GetUser reports a missing id');

  if failures > 0 then
  begin
    WriteLn(failures, ' failure(s)');
    Halt(1);
  end;
  WriteLn('all users tests passed');
end.
