{ test_core.pas — tests for the shared primitives. Not one of the two
  required domain tests, but cheap insurance since everything else depends
  on Core being right. }
program TestCore;

{$mode objfpc}{$H+}

uses
  Core;

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

begin
  Check(Base62Encode(0) = '0', 'Base62Encode(0) = "0"');
  Check(Base62Encode(61) = 'z', 'Base62Encode(61) = "z"');
  Check(Base62Encode(62) = '10', 'Base62Encode(62) = "10"');

  Check(IsNonEmptyTitle('Hello') = True, 'IsNonEmptyTitle accepts non-empty text');
  Check(IsNonEmptyTitle('   ') = False, 'IsNonEmptyTitle rejects whitespace-only');
  Check(IsNonEmptyTitle('') = False, 'IsNonEmptyTitle rejects empty string');

  Check(IsValidEmail('a@b.com') = True, 'IsValidEmail accepts a@b.com');
  Check(IsValidEmail('nodomain') = False, 'IsValidEmail rejects text with no @');
  Check(IsValidEmail('a@b') = False, 'IsValidEmail rejects a domain with no dot');
  Check(IsValidEmail('@b.com') = False, 'IsValidEmail rejects an empty local part');
  Check(IsValidEmail('a@b.com@c.com') = False, 'IsValidEmail rejects a second @');

  if failures > 0 then
  begin
    WriteLn(failures, ' failure(s)');
    Halt(1);
  end;
  WriteLn('all core tests passed');
end.
