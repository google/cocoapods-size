# CocoaPods Size Measurement

According to [this article](https://www.linkedin.com/pulse/top-12-reasons-why-users-frequently-uninstall-mobile-apps-fakhruddin/), the number one reason users uninstall apps is the size. Having a large app can significantly reduce adoption and retention (at the time of writing, apps over 150MB cannot be downloaded over a cellular network). As an SDK developer, it is even more critical to keep your library size in check, as app developers will refuse using your SDK if it adds too much bloat to their app.

This repository provides a set of tools which help with the measurement of the final binary size for the given set of CocoaPods.

## Usage examples

Measuring the size of the CocoaPod named AFNetworking using the latest released version:

```
./measure_cocoapod_size.py --cocoapods AFNetworking

// Output:
Size comes out to be 231568 bytes (measured at version 3.2.1)
```




Measuring the size of the AFNetworking CocoaPod at version 3.2.0:

```
./measure_cocoapod_size.py --cocoapods AFNetworking:3.2.0

// Output:
Size comes out to be 231544 bytes
```



Measuring the size of the FirebaseMessaging CocoaPod at version 3.0.2 with FirebaseAnalytics at version 5.0.0:

```
./measure_cocoapod_size.py --cocoapods FirebaseMessaging:3.0.2 FirebaseAnalytics:5.0.0

// Output:
Size comes to be 1800752 bytes. This is 298212 bytes less when measured together vs each measured individually due to shared dependencies.
```



Measuring the size of AFNetworking CocoaPod at version 3.2.0 present in your SPEC_REPO:

`./measure_cocoapod_size.py --cocoapods AFNetworking:3.2.0 --spec_repos SPEC_REPO`

Measuring the size of RxSwift CocoaPod which is a swift pod:

`./measure_cocoapod_size.py --cocoapods RxSwift --mode swift`

Finding the size between two Xcode projects:

`./xcode_project_diff.py --source_project=PROJECT1 --source_scheme=PROJECT1_SCHEME --target_project=PROJECT2 --target_scheme=PROJECT2_SCHEME`

### Measure pod size from local or bleeding edge version

Measuring the size of FirebaseDatabase CocoaPod from local:

```
./measure_cocoapod_size.py --cocoapods FirebaseDatabase --cocoapods_source_config "./source_config.json"
```
where the `source_config.json` is:
```
{
  "pods":[
    {
      "sdk":"FirebaseDatabase",
      "path":"~/Desktop/firebase-ios-sdk"
    }
  ]
}

```

Measuring the size of FirebaseDatabase CocoaPod from a branch of a remote repo:

```
./measure_cocoapod_size.py --cocoapods FirebaseDatabase --cocoapods_source_config "./source_config.json"
```
where the `source_config.json` is:
```
{
  "pods":[
    {
      "sdk":"FirebaseDatabase",
      "git":"https://github.com/firebase/firebase-ios-sdk",
      "branch":"master"
    }
  ]
}

```



## Available Tools

### measure_cocoapod_size.py

`./measure_cocoapod_size.py --cocoapods $POD_NAME:$POD_VERSION $POD_NAME1:$POD_VERSION1 -mode $POD_TYPE`

This tool provides the size measurement given a combination of CocoaPods. This tool internally uses the xcode_project_diff.py tool.
Please use `./measure_cocoapod_size.py -h` to get the full usage description and a complete list of the available flags.

### xcode_project_diff.py

`./xcode_project_diff.py --source_project=$SOURCE_PROJECT --source_scheme=$SOURCE_SCHEME --target_project=$TARGET_PROJECT --target_scheme=$TARGET_SCHEME`

This tool takes in two Xcode project targets and provides the size difference between the two Xcode project targets. Please use `./xcode_project_diff.py -h` to get the full usage description and a complete list of the available flags.


## Methodology

Our methodology involves doing the following:
- Archive a baseline app as ARM64 with no bitcode
- Add the SDKs we wanted to measure
- Archive a baseline app as ARM64 with no bitcode
- Compute the difference and report on it

For example, using this method for FirebaseAnalytics 5.0.1, we obtain the following number: **1,082,948** which estimates the install size.

iTunes Connect reports both download and install sizes for apps in TestFlight. We have used this to instrument a standalone app, and measured it before and after adding FirebaseAnalytics. The numbers we found here are close to our measurements.

For example, for iPhone 6S:
Download size: **925 KiB**
Install size: **1094 KiB**

The install size is within a range of 3% from our measurements.
