AVO AVHRR Processing
====================


A suite of tools to produce AVHRR images for volcview when new data has been retrieved.


```mermaid
flowchart LR
    download_avhrr[[download_avhrr]] -- AvhrrL1Topic--> check_coverage[[check_coverage]]
    check_coverage -- AvhrrImageQueue --> produce-image[[produce-image]]
    produce-image -- AvhrrPngTopic --> post-volcview[[post-volcview]]
```
