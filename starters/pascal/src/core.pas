{ core.pas — Design D's ONE home for cross-cutting primitives.

  Every capability declared here (base62 id encoding, title/email validation)
  must be implemented exactly once, in this file. Domain units (Users, Tasks)
  are only allowed to *call* these functions via `uses Core;` — they must
  never re-implement them. tools/boundary_lint.sh enforces that by scanning
  every other .pas file for a matching function/procedure definition. }
unit Core;

{$mode objfpc}{$H+}

interface

const
  Base62Alphabet: string =
    '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';

{ Encodes a non-negative integer as a base62 string. This is the only
  id-encoding primitive in the repo; Users and Tasks both call it instead
  of rolling their own. }
function Base62Encode(Value: Int64): string;

{ A "title" is valid if it has at least one non-whitespace character.
  Used by Users (person name) and Tasks (task title) alike. }
function IsNonEmptyTitle(const Title: string): Boolean;

{ A minimal but real email check: exactly one '@', a non-empty local part,
  and a domain part containing a '.' with characters on both sides. }
function IsValidEmail(const Email: string): Boolean;

implementation

uses SysUtils;

function Base62Encode(Value: Int64): string;
var
  n: Int64;
  digit: Integer;
begin
  if Value <= 0 then
  begin
    Result := '0';
    Exit;
  end;
  Result := '';
  n := Value;
  while n > 0 do
  begin
    digit := n mod 62;
    Result := Base62Alphabet[digit + 1] + Result;
    n := n div 62;
  end;
end;

function IsNonEmptyTitle(const Title: string): Boolean;
begin
  Result := Length(Trim(Title)) > 0;
end;

function IsValidEmail(const Email: string): Boolean;
var
  AtPos, DotPos: Integer;
  Local, Domain: string;
begin
  Result := False;

  if Pos(' ', Email) > 0 then
    Exit;

  AtPos := Pos('@', Email);
  if (AtPos <= 1) or (AtPos = Length(Email)) then
    Exit; { no '@', or '@' glued to the start/end }

  Local := Copy(Email, 1, AtPos - 1);
  Domain := Copy(Email, AtPos + 1, Length(Email) - AtPos);

  if Pos('@', Domain) > 0 then
    Exit; { more than one '@' }

  if Length(Local) = 0 then
    Exit;

  DotPos := Pos('.', Domain);
  if (DotPos <= 1) or (DotPos = Length(Domain)) then
    Exit; { domain needs "x.y", not ".y", "x.", or no dot at all }

  Result := True;
end;

end.
