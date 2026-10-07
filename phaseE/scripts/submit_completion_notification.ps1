param([switch]$ValidateOnly, [string]$MessagePath = 'D:\论文集\phaseE\_completion_notification\message.json')
$ErrorActionPreference = 'Stop'
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime] | Out-Null
[Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType=WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType=WindowsRuntime] | Out-Null
if ($ValidateOnly) {
    $message = @{title='Notification interface check';body='No notification is displayed in this mode.'}
} else {
    $message = [System.IO.File]::ReadAllText($MessagePath,[System.Text.Encoding]::UTF8) | ConvertFrom-Json
}
$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml('<toast activationType="protocol" launch="https://github.com/PaperDiamond448/acoustic-trajectory-autofocus-paper/tree/main/phaseE"><visual><binding template="ToastGeneric"><text/><text/></binding></visual></toast>')
$nodes = $xml.GetElementsByTagName('text')
$nodes.Item(0).AppendChild($xml.CreateTextNode([string]$message.title)) | Out-Null
$nodes.Item(1).AppendChild($xml.CreateTextNode([string]$message.body)) | Out-Null
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
$toast.ExpirationTime = [DateTimeOffset]::Now.AddDays(1)
$notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Microsoft.Windows.PowerShell')
if ($null -eq $notifier) { throw 'Windows notification interface is unavailable.' }
if ($ValidateOnly) {
    Write-Output 'Notification object and Windows interface validated; nothing displayed.'
} else {
    $notifier.Show($toast)
    Write-Output 'Notification submitted to Windows.'
}
