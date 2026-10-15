[CmdletBinding()]
param(
    [string]$Port = 'COM3',
    [Parameter(Mandatory)][string]$Log,
    [ValidateRange(10,3600)][int]$TimeoutSeconds = 120
)
$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$taskLog = [IO.Path]::GetFullPath((Join-Path $taskRoot $Log))
if (!$taskLog.StartsWith((Join-Path $taskRoot 'results') + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Capture must stay inside project results'
}
if (Test-Path -LiteralPath $taskLog) { throw 'Refuse existing capture; preserve every attempt' }
Add-Type -AssemblyName System.IO.Ports
New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($taskLog)) -Force | Out-Null
$taskSerial = [IO.Ports.SerialPort]::new($Port,115200,[IO.Ports.Parity]::None,8,[IO.Ports.StopBits]::One)
$taskSerial.Handshake = [IO.Ports.Handshake]::None
$taskSerial.DtrEnable = $false
$taskSerial.RtsEnable = $false
$taskSerial.ReadTimeout = 200
$taskCapture = [ordered]@{status='OPENING_PORT_NOT_BOARD_RESULT';port=$Port;baud=115200;data_bits=8;parity='None';stop_bits=1;handshake='None';method='Windows System.IO.Ports raw byte capture';log=$taskLog;started_utc=[DateTime]::UtcNow.ToString('o');bytes=0}
$taskFile = $null
try {
    $taskSerial.Open()
    $taskSerial.DiscardInBuffer()
    $taskFile = [IO.File]::Open($taskLog,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
    $taskCapture.status='READY_FOR_SINGLE_CASE_PROGRAMMING'
    $taskCapture | ConvertTo-Json | Set-Content -LiteralPath "$taskLog.capture.json" -Encoding utf8NoBOM
    Write-Host "UART READY: $Port,115200,8N1,handshakeOFF. Raw log: $taskLog"
    Write-Host 'Only one workload/configuration. No programming, reset or next case is performed by this receiver.'
    $taskClock = [Diagnostics.Stopwatch]::StartNew()
    $taskBuffer = [byte[]]::new(4096)
    $taskText = ''
    while ($taskClock.Elapsed.TotalSeconds -lt $TimeoutSeconds) {
        if ($taskSerial.BytesToRead -gt 0) {
            $taskRead = $taskSerial.Read($taskBuffer,0,[math]::Min($taskBuffer.Length,$taskSerial.BytesToRead))
            $taskFile.Write($taskBuffer,0,$taskRead); $taskFile.Flush()
            $taskCapture.bytes += $taskRead
            $taskChunk = [Text.Encoding]::ASCII.GetString($taskBuffer,0,$taskRead)
            Write-Host -NoNewline $taskChunk
            $taskText += $taskChunk
            if ($taskCapture.bytes -gt 1048576) { throw 'Capture bound exceeded; raw bytes retained' }
            if ($taskText -match '(?m)^DONE\r?$') {
                $taskCapture.status='CAPTURED_DONE_REQUIRES_UART_CHECK_AND_OWNER_CONFIRMATION'
                break
            }
        }
        Start-Sleep -Milliseconds 20
    }
    if ($taskCapture.status -eq 'READY_FOR_SINGLE_CASE_PROGRAMMING') {
        $taskCapture.status='TIMEOUT_RAW_CAPTURE_RETAINED'
    }
} catch {
    $taskCapture.status='CAPTURE_FAILED_REQUIRES_INSPECTION'
    $taskCapture.error=$_.Exception.Message
    throw
} finally {
    if ($taskFile) { $taskFile.Dispose() }
    if ($taskSerial.IsOpen) { $taskSerial.Close() }
    $taskSerial.Dispose()
    $taskCapture.completed_utc=[DateTime]::UtcNow.ToString('o')
    $taskCapture | ConvertTo-Json | Set-Content -LiteralPath "$taskLog.capture.json" -Encoding utf8NoBOM
    Write-Host "`n$($taskCapture.status). Stop here for physical LEDR/HEX and owner confirmation."
}
