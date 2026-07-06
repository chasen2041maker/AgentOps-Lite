param(
    [string] $OutputPath = "assets/demo.gif"
)

$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Drawing

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$frameDir = Join-Path $repoRoot (Join-Path ".tmp" ("demo-gif-frames-" + $PID))
New-Item -ItemType Directory -Path $frameDir | Out-Null

function Resolve-Ffmpeg {
    $cmd = Get-Command ffmpeg -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }

    $wingetPackages = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages"
    $match = Get-ChildItem -Path $wingetPackages -Recurse -Filter ffmpeg.exe -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($match) {
        return $match.FullName
    }

    throw "ffmpeg.exe was not found. Install Gyan.FFmpeg or add ffmpeg to PATH."
}

function New-Brush([string] $hex) {
    $r = [Convert]::ToInt32($hex.Substring(1, 2), 16)
    $g = [Convert]::ToInt32($hex.Substring(3, 2), 16)
    $b = [Convert]::ToInt32($hex.Substring(5, 2), 16)
    return [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb($r, $g, $b))
}

function Draw-Text($graphics, [string] $text, [int] $x, [int] $y, $font, $brush) {
    $graphics.DrawString($text, $font, $brush, [System.Drawing.PointF]::new($x, $y))
}

function Draw-Terminal-Frame([string] $path, [int] $stage) {
    $width = 1000
    $height = 640
    $bitmap = [System.Drawing.Bitmap]::new($width, $height)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::ClearTypeGridFit

    $bg = New-Brush "#0f172a"
    $panel = New-Brush "#111827"
    $borderPen = [System.Drawing.Pen]::new([System.Drawing.ColorTranslator]::FromHtml("#334155"), 2)
    $mutedPen = [System.Drawing.Pen]::new([System.Drawing.ColorTranslator]::FromHtml("#475569"), 2)
    $arrowPen = [System.Drawing.Pen]::new([System.Drawing.ColorTranslator]::FromHtml("#38bdf8"), 4)
    $arrowPen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
    $arrowPen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round

    $white = New-Brush "#f8fafc"
    $muted = New-Brush "#cbd5e1"
    $red = New-Brush "#fca5a5"
    $green = New-Brush "#86efac"
    $yellow = New-Brush "#fde68a"
    $cyan = New-Brush "#7dd3fc"

    $font = [System.Drawing.Font]::new("Consolas", 18, [System.Drawing.FontStyle]::Regular)
    $bold = [System.Drawing.Font]::new("Consolas", 18, [System.Drawing.FontStyle]::Bold)
    $small = [System.Drawing.Font]::new("Consolas", 14, [System.Drawing.FontStyle]::Regular)
    $footer = [System.Drawing.Font]::new("Consolas", 15, [System.Drawing.FontStyle]::Regular)

    $graphics.FillRectangle($bg, 0, 0, $width, $height)
    $graphics.DrawRectangle($borderPen, 1, 1, $width - 2, $height - 2)
    $graphics.FillEllipse((New-Brush "#ef4444"), 32, 27, 14, 14)
    $graphics.FillEllipse((New-Brush "#f59e0b"), 56, 27, 14, 14)
    $graphics.FillEllipse((New-Brush "#22c55e"), 80, 27, 14, 14)

    Draw-Text $graphics "python examples/financial_report_demo/run.py" 116 24 $small $muted

    if ($stage -ge 1) {
        Draw-Text $graphics "Before GroundGuard correction" 52 82 $bold $white
        $graphics.DrawLine($mutedPen, 52, 114, 352, 114)
        Draw-Text $graphics "passed: False" 52 140 $font $red
        Draw-Text $graphics "verified: 0" 52 178 $font $muted
        Draw-Text $graphics "unverified: 0" 52 216 $font $muted
        Draw-Text $graphics "contradicted: 0" 52 254 $font $muted
        Draw-Text $graphics "omitted_required: 2" 52 292 $font $red
        Draw-Text $graphics "policy_reason:" 52 330 $font $yellow
        Draw-Text $graphics "omitted_required_count=2" 52 368 $font $yellow
    }

    if ($stage -ge 2) {
        $graphics.DrawLine($arrowPen, 444, 260, 536, 260)
        $graphics.DrawLine($arrowPen, 516, 240, 536, 260)
        $graphics.DrawLine($arrowPen, 516, 280, 536, 260)
    }

    if ($stage -ge 3) {
        Draw-Text $graphics "After fact-key correction" 604 82 $bold $white
        $graphics.DrawLine($mutedPen, 604, 114, 884, 114)
        Draw-Text $graphics "passed: True" 604 140 $font $green
        Draw-Text $graphics "verified: 2" 604 178 $font $green
        Draw-Text $graphics "unverified: 0" 604 216 $font $muted
        Draw-Text $graphics "contradicted: 0" 604 254 $font $muted
        Draw-Text $graphics "omitted_required: 0" 604 292 $font $green
    }

    if ($stage -ge 4) {
        $graphics.FillRectangle($panel, 52, 550, 876, 42)
        Draw-Text $graphics "Local fact gate: required facts cannot quietly disappear." 70 560 $footer $cyan
    }

    $bitmap.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
    $graphics.Dispose()
    $bitmap.Dispose()
}

$frames = @(
    @{ Stage = 0; Duration = "0.7" },
    @{ Stage = 1; Duration = "1.6" },
    @{ Stage = 2; Duration = "0.7" },
    @{ Stage = 3; Duration = "1.6" },
    @{ Stage = 4; Duration = "2.6" }
)

$concatPath = Join-Path $frameDir "frames.txt"
$concatLines = @()
for ($i = 0; $i -lt $frames.Count; $i++) {
    $framePath = Join-Path $frameDir ("frame_{0:D3}.png" -f $i)
    Draw-Terminal-Frame $framePath $frames[$i].Stage
    $escapedPath = $framePath.Replace("\", "/")
    $concatLines += "file '$escapedPath'"
    $concatLines += "duration $($frames[$i].Duration)"
}

$lastFrame = (Join-Path $frameDir ("frame_{0:D3}.png" -f ($frames.Count - 1))).Replace("\", "/")
$concatLines += "file '$lastFrame'"
$concatLines | Set-Content -Encoding ASCII $concatPath

$ffmpeg = Resolve-Ffmpeg
$resolvedOutput = Join-Path $repoRoot $OutputPath
& $ffmpeg -y -f concat -safe 0 -i $concatPath -vf "fps=12,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" $resolvedOutput

Write-Host "Wrote $resolvedOutput"
