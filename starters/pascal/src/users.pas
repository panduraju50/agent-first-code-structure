{ users.pas — the Users domain.

  Design D rule 2: a domain may depend on core, never on another domain.
  This unit's `uses` clause names Core only. It has no idea Tasks exists,
  and never will — tasks.pas.AssignTask takes a plain UserId string, so
  there is nothing here for a Tasks-side dependency to attach to. }
unit Users;

{$mode objfpc}{$H+}

interface

type
  TUser = record
    Id: string;
    Name: string;
    Email: string;
  end;

  TUserArray = array of TUser;

  TUserStore = record
    Items: TUserArray;
    NextId: Int64;
  end;

{ Validates Name/Email via Core, then mints an id via Core.Base62Encode.
  Returns False (with ErrMsg set) instead of raising, so callers — including
  the composition root — decide how to react. }
function CreateUser(var Store: TUserStore; const Name, Email: string;
  out NewUser: TUser; out ErrMsg: string): Boolean;

function GetUser(const Store: TUserStore; const Id: string;
  out FoundUser: TUser): Boolean;

implementation

uses Core;

function CreateUser(var Store: TUserStore; const Name, Email: string;
  out NewUser: TUser; out ErrMsg: string): Boolean;
begin
  Result := False;
  NewUser.Id := '';
  NewUser.Name := '';
  NewUser.Email := '';
  ErrMsg := '';

  if not Core.IsNonEmptyTitle(Name) then
  begin
    ErrMsg := 'user name must not be empty';
    Exit;
  end;

  if not Core.IsValidEmail(Email) then
  begin
    ErrMsg := 'email is not valid: ' + Email;
    Exit;
  end;

  Inc(Store.NextId);
  NewUser.Id := 'u_' + Core.Base62Encode(Store.NextId);
  NewUser.Name := Name;
  NewUser.Email := Email;

  SetLength(Store.Items, Length(Store.Items) + 1);
  Store.Items[High(Store.Items)] := NewUser;
  Result := True;
end;

function GetUser(const Store: TUserStore; const Id: string;
  out FoundUser: TUser): Boolean;
var
  i: Integer;
begin
  Result := False;
  for i := 0 to High(Store.Items) do
    if Store.Items[i].Id = Id then
    begin
      FoundUser := Store.Items[i];
      Result := True;
      Exit;
    end;
end;

end.
