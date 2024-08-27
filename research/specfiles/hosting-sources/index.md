---
title: Hosting sources for Fedora
authors: mfocko
---

:::tip Context

tl;dr As long as Packit is deployed on the MP+, onboarding of new users is
limited by the firewall rules that need to be explicitly allowed. Additionally
firewall is mostly blocking `sync-release` actions specifically.

This is outcome of [this](https://github.com/packit/packit-service/issues/2390)
issue.

:::

All `SourceX` fields of the specfiles have been initially scraped by the @msuchy.
This “research” provides the scripts that have been used to process the scraped
sources.

### Domains with ≥ 10 occurrences

| count | domains                                                                                                                                         |
| ----: | ----------------------------------------------------------------------------------------------------------------------------------------------- |
|    10 | kokkinizita.linuxaudio.org netfilter.org dl.suckless.org downloads.xiph.org netlib.org forge.puppet.com                                         |
|    11 | launchpad.net red-bean.com users.teilar.gr gstreamer.freedesktop.org spice-space.org dist.schmorp.de                                            |
|    12 | repo1.maven.org archive.apache.org download.tuxfamily.org downloads.isc.org festvox.org libsdl.org cpan.metacpan.org                            |
|    13 | savannah.nongnu.org identicalsoftware.com people.redhat.com gnu.org marlam.de downloads.xiph.org download.fcitx-im.org frama-c.com erratique.ch |
|    14 | ftp.debian.org xorg.freedesktop.org pari.math.u-bordeaux.fr developers.yubico.com ftp.samba.org software.sil.org ftp.cpc.ncep.noaa.gov          |
|    15 | ftp.de.debian.org freedesktop.org invisible-island.net docbook.org                                                                              |
|    16 | invent.kde.org ftp.postgresql.org                                                                                                               |
|    17 | dev-www.libreoffice.org emersion.fr cran.r-project.org                                                                                          |
|    18 | salsa.debian.org kernel.org codeberg.org xorg.freedesktop.org                                                                                   |
|    19 | cpan.org                                                                                                                                        |
|    20 | git.kernel.org                                                                                                                                  |
|    22 | prdownloads.sourceforge.net pgp.key-server.io python.org cran.r-project.org                                                                     |
|    25 | gnupg.org                                                                                                                                       |
|    28 | launchpad.net download.services.openoffice.org                                                                                                  |
|    30 | apache.org greekfontsociety-gfs.gr bioconductor.org xine.sourceforge.net                                                                        |
|    31 | keys.openpgp.org                                                                                                                                |
|    32 | apache.org kernel.org                                                                                                                           |
|    32 | download.sugarlabs.org pear.php.net                                                                                                             |
|    33 | downloads.sf.net                                                                                                                                |
|    34 | download.sourceforge.net pub.mate-desktop.org                                                                                                   |
|    35 | fedorahosted.org pypi.python.org                                                                                                                |
|    36 | archive.apache.org                                                                                                                              |
|    40 | download.savannah.gnu.org git.sr.ht                                                                                                             |
|    41 | ftp.gnome.org download.qt.io                                                                                                                    |
|    42 | pecl.php.net                                                                                                                                    |
|    43 | ftp.gnu.org                                                                                                                                     |
|    44 | download.fcitx-im.org                                                                                                                           |
|    45 | pagure.io releases.openstack.org                                                                                                                |
|    46 | sourceforge.net                                                                                                                                 |
|    50 | bitbucket.org                                                                                                                                   |
|    51 | ftp.kde.org                                                                                                                                     |
|    53 | pypi.io                                                                                                                                         |
|    59 | repo.gridcf.org rubygems.org                                                                                                                    |
|    60 | gitlab.gnome.org                                                                                                                                |
|    61 | releases.pagure.org                                                                                                                             |
|    63 | archive.xfce.org                                                                                                                                |
|    64 | sourceforge.net                                                                                                                                 |
|    66 | gitlab.freedesktop.org                                                                                                                          |
|    67 | download.gnome.org                                                                                                                              |
|    72 | download.qt.io                                                                                                                                  |
|    87 | downloads.asterisk.org                                                                                                                          |
|    88 | tarballs.openstack.org                                                                                                                          |
|    90 | pypi.python.org                                                                                                                                 |
|   120 | x.org                                                                                                                                           |
|   148 | repo1.maven.org                                                                                                                                 |
|   160 | downloads.sourceforge.net                                                                                                                       |
|   168 | ftp.gnu.org                                                                                                                                     |
|   183 | gitlab.com                                                                                                                                      |
|   253 | download.gnome.org                                                                                                                              |
|   327 | cran.r-project.org                                                                                                                              |
|   387 | rubygems.org                                                                                                                                    |
|   621 | downloads.sourceforge.net                                                                                                                       |
|   663 | download.kde.org                                                                                                                                |
|   910 | hackage.haskell.org                                                                                                                             |
|  1510 | files.pythonhosted.org                                                                                                                          |
|  2734 | crates.io                                                                                                                                       |
|  3008 | cpan.metacpan.org                                                                                                                               |
|  8145 | ctan.math.illinois.edu                                                                                                                          |
|  8770 | github.com                                                                                                                                      |

### Domains with issues (ran locally…)

<details>

```
2024/07/16 13:07:34 [INFO] Starting the checks…
2024/07/16 13:07:51 [FAIL] ‹https://gitlab.freedesktop.org› with ‹Get "https://gitlab.freedesktop.org/explore/groups": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:08:09 [FAIL] ‹https://pgp.key-server.io› with ‹Get "https://pgp.key-server.io": dial tcp: lookup pgp.key-server.io: no such host›
2024/07/16 13:08:40 [FAIL] ‹http://users.teilar.gr› with ‹Get "http://users.teilar.gr": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:08:58 [FAIL] ‹http://download.gna.org› with ‹Get "http://download.gna.org": dial tcp: lookup download.gna.org: no such host›
2024/07/16 13:09:08 [FAIL] ‹https://ftp.pcre.org› with ‹Get "https://ftp.pcre.org": dial tcp: lookup ftp.pcre.org: no such host›
2024/07/16 13:09:13 [FAIL] ‹http://dl.sourceforge.net› with ‹Get "http://dl.sourceforge.net": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:09:16 [FAIL] ‹http://ncdgames.t3-i.com› with ‹Get "http://ncdgames.t3-i.com": dial tcp: lookup ncdgames.t3-i.com: no such host›
2024/07/16 13:09:18 [FAIL] ‹http://shorewall.net› with ‹Get "http://shorewall.net": dial tcp: lookup shorewall.net: no such host›
2024/07/16 13:09:20 [FAIL] ‹http://android.git.kernel.org› with ‹Get "http://android.git.kernel.org": dial tcp: lookup android.git.kernel.org: no such host›
2024/07/16 13:09:23 [FAIL] ‹https://math.rwth-aachen.de› with ‹Get "https://math.rwth-aachen.de": dial tcp: lookup math.rwth-aachen.de: no such host›
2024/07/16 13:09:30 [FAIL] ‹http://dl.sf.net› with ‹Get "http://dl.sf.net": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:09:37 [FAIL] ‹http://dl.sourceforge.jp› with ‹Get "http://dl.sourceforge.jp": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:09:39 [FAIL] ‹http://tiresias.org› with ‹Get "https://tiresias.org/": tls: failed to verify certificate: x509: certificate has expired or is not yet valid: current time 2024-07-16T13:09:39+02:00 is after 2024-06-11T23:25:40Z›
2024/07/16 13:10:01 [FAIL] ‹http://abisource.com› with ‹Get "http://abisource.com": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:10:01 [FAIL] ‹http://thibault.org› with ‹Get "http://thibault.org": dial tcp 207.192.74.119:80: connect: connection refused›
2024/07/16 13:10:10 [FAIL] ‹http://wanderinghorse.net› with ‹Get "http://wanderinghorse.net": dial tcp 194.195.245.37:80: connect: connection refused›
2024/07/16 13:10:19 [FAIL] ‹http://downloads.sourceforge.jp› with ‹Get "http://downloads.sourceforge.jp": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:10:21 [FAIL] ‹http://info.openlab.ipa.go.jp› with ‹Get "http://info.openlab.ipa.go.jp": dial tcp: lookup info.openlab.ipa.go.jp: no such host›
2024/07/16 13:10:22 [FAIL] ‹http://geolite.maxmind.com› with ‹Get "http://geolite.maxmind.com": dial tcp: lookup geolite.maxmind.com: no such host›
2024/07/16 13:10:52 [FAIL] ‹http://dilvie.com› with ‹Get "http://dilvie.com": dial tcp: lookup dilvie.com: no such host›
2024/07/16 13:11:04 [FAIL] ‹http://blargg.fileave.com› with ‹Get "http://blargg.fileave.com": EOF›
2024/07/16 13:11:04 [FAIL] ‹https://remlab.net› with ‹Get "https://remlab.net": dial tcp: lookup remlab.net: no such host›
2024/07/16 13:11:16 [FAIL] ‹https://infradead.org› with ‹Get "https://infradead.org": dial tcp: lookup infradead.org: no such host›
2024/07/16 13:11:16 [FAIL] ‹https://mirbsd.org› with ‹Get "https://mirbsd.org": dial tcp: lookup mirbsd.org: no such host›
2024/07/16 13:11:18 [FAIL] ‹http://gitatsu.hp.infoseek.co.jp› with ‹Get "http://gitatsu.hp.infoseek.co.jp": dial tcp: lookup gitatsu.hp.infoseek.co.jp: no such host›
2024/07/16 13:11:23 [FAIL] ‹http://kanji.zinbun.kyoto-u.ac.jp› with ‹Get "http://kanji.zinbun.kyoto-u.ac.jp": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:11:31 [FAIL] ‹https://geolite.maxmind.com› with ‹Get "https://geolite.maxmind.com": dial tcp: lookup geolite.maxmind.com: no such host›
2024/07/16 13:11:31 [FAIL] ‹https://math.uni-bielefeld.de› with ‹Get "https://math.uni-bielefeld.de": dial tcp: lookup math.uni-bielefeld.de: no such host›
2024/07/16 13:11:38 [FAIL] ‹http://brouhaha.com› with ‹Get "http://brouhaha.com": dial tcp: lookup brouhaha.com: no such host›
2024/07/16 13:11:46 [FAIL] ‹https://cryptopp.com› with ‹Get "https://cryptopp.com": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:11:51 [FAIL] ‹http://litech.org› with ‹Get "http://litech.org": dial tcp: lookup litech.org: no such host›
2024/07/16 13:11:52 [FAIL] ‹https://lab.louiz.org› with ‹Get "https://lab.louiz.org": dial tcp 51.15.8.47:443: connect: connection refused›
2024/07/16 13:11:58 [FAIL] ‹http://crl.nmsu.edu› with ‹Get "http://crl.nmsu.edu": dial tcp: lookup crl.nmsu.edu: no such host›
2024/07/16 13:12:03 [FAIL] ‹http://corpit.ru› with ‹Get "http://corpit.ru": dial tcp: lookup corpit.ru: no such host›
2024/07/16 13:12:03 [FAIL] ‹http://let.rug.nl› with ‹Get "http://let.rug.nl": dial tcp: lookup let.rug.nl: no such host›
2024/07/16 13:12:19 [FAIL] ‹https://music.mcgill.ca› with ‹Get "https://music.mcgill.ca": dial tcp: lookup music.mcgill.ca: no such host›
2024/07/16 13:12:43 [FAIL] ‹http://pcc.ludd.ltu.se› with ‹Get "http://pcc.ludd.ltu.se": dial tcp 130.240.207.127:80: connect: no route to host›
2024/07/16 13:12:47 [FAIL] ‹http://opendnssec.org› with ‹Get "http://opendnssec.org": dial tcp: lookup opendnssec.org: no such host›
2024/07/16 13:12:50 [FAIL] ‹https://ftp.infradead.org› with ‹Get "https://ftp.infradead.org": tls: failed to verify certificate: x509: certificate is valid for casper.infradead.org, git.infradead.org, lists.infradead.org, lists.openwrt.org, ns1.infradead.org, smtpauth.infradead.org, www.infradead.org, not ftp.infradead.org›
2024/07/16 13:12:55 [FAIL] ‹https://dl.opendesktop.org› with ‹Get "https://dl.opendesktop.org": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:12:55 [FAIL] ‹http://thessalonica.org.ru› with ‹Get "http://thessalonica.org.ru": dial tcp: lookup thessalonica.org.ru: no such host›
2024/07/16 13:12:57 [FAIL] ‹http://src.linuxhacker.at› with ‹Get "http://src.linuxhacker.at": dial tcp: lookup src.linuxhacker.at: no such host›
2024/07/16 13:13:33 [FAIL] ‹http://alioth.debian.org› with ‹Get "http://alioth.debian.org": dial tcp: lookup alioth.debian.org: no such host›
2024/07/16 13:13:34 [FAIL] ‹http://switch.dl.sourceforge.net› with ‹Get "http://switch.dl.sourceforge.net": dial tcp: lookup switch.dl.sourceforge.net: no such host›
2024/07/16 13:13:42 [FAIL] ‹http://plugin.org.uk› with ‹Get "http://plugin.org.uk": dial tcp 208.113.196.132:80: i/o timeout (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:13:42 [FAIL] ‹https://dockapps.net› with ‹Get "https://dockapps.net": tls: failed to verify certificate: x509: certificate is valid for *.github.com, github.com, not dockapps.net›
2024/07/16 13:13:47 [FAIL] ‹http://unix-ag.uni-kl.de› with ‹Get "http://unix-ag.uni-kl.de": dial tcp: lookup unix-ag.uni-kl.de: no such host›
2024/07/16 13:13:50 [FAIL] ‹http://cl.cam.ac.uk› with ‹Get "http://cl.cam.ac.uk": dial tcp: lookup cl.cam.ac.uk: no such host›
2024/07/16 13:13:50 [FAIL] ‹http://coyotegulch.com› with ‹Get "http://coyotegulch.com": EOF›
2024/07/16 13:13:50 [FAIL] ‹http://isl.gforge.inria.fr› with ‹Get "http://isl.gforge.inria.fr": dial tcp: lookup isl.gforge.inria.fr: no such host›
2024/07/16 13:13:59 [FAIL] ‹https://media.inkscape.org› with ‹Get "https://inkscape.org/": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:14:00 [FAIL] ‹https://alioth.debian.org› with ‹Get "https://alioth.debian.org": dial tcp: lookup alioth.debian.org: no such host›
2024/07/16 13:14:06 [FAIL] ‹https://ayera.dl.sourceforge.net› with ‹Get "https://ayera.dl.sourceforge.net": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:14:09 [FAIL] ‹http://fo.speling.org› with ‹Get "http://fo.speling.org": dial tcp: lookup fo.speling.org: no such host›
2024/07/16 13:14:16 [FAIL] ‹http://hping.org› with ‹Get "http://hping.org": dial tcp 192.81.221.216:80: i/o timeout (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:14:19 [FAIL] ‹http://nco.ncep.noaa.gov› with ‹Get "http://nco.ncep.noaa.gov": dial tcp: lookup nco.ncep.noaa.gov: no such host›
2024/07/16 13:14:21 [FAIL] ‹http://upperbounds.net› with ‹Get "http://127.0.0.1": dial tcp 127.0.0.1:80: connect: connection refused›
2024/07/16 13:14:21 [FAIL] ‹http://5b4az.chronos.org.uk› with ‹Get "http://5b4az.chronos.org.uk": dial tcp: lookup 5b4az.chronos.org.uk: no such host›
2024/07/16 13:14:23 [FAIL] ‹http://downloads.grantlee.org› with ‹Get "http://downloads.grantlee.org": dial tcp: lookup downloads.grantlee.org: no such host›
2024/07/16 13:14:26 [FAIL] ‹http://complang.tuwien.ac.at› with ‹Get "https://complang.tuwien.ac.at/": tls: failed to verify certificate: x509: certificate signed by unknown authority›
2024/07/16 13:14:27 [FAIL] ‹http://keys.gnupg.net› with ‹Get "http://keys.gnupg.net": dial tcp: lookup keys.gnupg.net: no such host›
2024/07/16 13:14:28 [FAIL] ‹http://kent.dl.sourceforge.net› with ‹Get "http://kent.dl.sourceforge.net": dial tcp: lookup kent.dl.sourceforge.net: no such host›
2024/07/16 13:14:31 [FAIL] ‹https://math.colostate.edu› with ‹Get "https://math.colostate.edu": dial tcp: lookup math.colostate.edu: no such host›
2024/07/16 13:14:32 [FAIL] ‹https://ljll.math.upmc.fr› with ‹Get "https://ljll.math.upmc.fr": tls: failed to verify certificate: x509: certificate signed by unknown authority›
2024/07/16 13:14:37 [FAIL] ‹http://daughtersoftiresias.org› with ‹Get "http://daughtersoftiresias.org": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:14:58 [FAIL] ‹https://cs.auckland.ac.nz› with ‹Get "https://www.auckland.ac.nz/en/science/about-the-faculty/school-of-computer-science.html": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:15:01 [FAIL] ‹http://fefe.de› with ‹Get "http://fefe.de": dial tcp: lookup fefe.de: no such host›
2024/07/16 13:15:02 [FAIL] ‹http://mavetju.org› with ‹Get "http://mavetju.org": dial tcp: lookup mavetju.org: no such host›
2024/07/16 13:15:05 [FAIL] ‹http://moria.de› with ‹Get "http://moria.de": dial tcp: lookup moria.de: no such host›
2024/07/16 13:15:11 [FAIL] ‹http://cloud.github.com› with ‹Get "http://cloud.github.com": dial tcp: lookup cloud.github.com: no such host›
2024/07/16 13:15:23 [FAIL] ‹http://distribute.atmel.no› with ‹Get "http://distribute.atmel.no": dial tcp: lookup distribute.atmel.no: no such host›
2024/07/16 13:15:36 [FAIL] ‹http://osdn.dl.sourceforge.jp› with ‹Get "http://osdn.dl.sourceforge.jp": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:15:39 [FAIL] ‹http://pps.univ-paris-diderot.fr› with ‹Get "http://pps.univ-paris-diderot.fr": dial tcp: lookup pps.univ-paris-diderot.fr: no such host›
2024/07/16 13:15:47 [FAIL] ‹http://tablix.org› with ‹Get "http://tablix.org": dial tcp: lookup tablix.org: no such host›
2024/07/16 13:15:57 [FAIL] ‹http://zenon-prover.org› with ‹Get "http://zenon-prover.org": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:16:03 [FAIL] ‹http://impul.se› with ‹Get "http://impul.se": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:16:05 [FAIL] ‹http://jmknoble.net› with ‹Get "http://jmknoble.net": dial tcp: lookup jmknoble.net: no such host›
2024/07/16 13:16:10 [FAIL] ‹http://download.sourceforge.jp› with ‹Get "http://download.sourceforge.jp": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:16:13 [FAIL] ‹http://webstaff.itn.liu.se› with ‹Get "http://webstaff.itn.liu.se": dial tcp: lookup webstaff.itn.liu.se: no such host›
2024/07/16 13:16:14 [FAIL] ‹http://xskat.de› with ‹Get "http://xskat.de": dial tcp: lookup xskat.de: no such host›
2024/07/16 13:16:17 [FAIL] ‹https://xrootd.slac.stanford.edu› with ‹Get "https://xrootd.slac.stanford.edu": tls: failed to verify certificate: x509: certificate signed by unknown authority›
2024/07/16 13:16:19 [FAIL] ‹http://pogo.org.uk› with ‹Get "http://pogo.org.uk": dial tcp: lookup pogo.org.uk: no such host›
2024/07/16 13:16:42 [FAIL] ‹https://people-mozilla.org› with ‹Get "https://people-mozilla.org": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:16:50 [FAIL] ‹http://neil.brown.name› with ‹Get "http://blog.neil.brown.name/": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:16:57 [FAIL] ‹http://downloads.laffeycomputer.com› with ‹Get "http://downloads.laffeycomputer.com": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:16:59 [FAIL] ‹http://async.com.br› with ‹Get "http://async.com.br": dial tcp: lookup async.com.br: no such host›
2024/07/16 13:17:05 [FAIL] ‹http://atnf.csiro.au› with ‹Get "http://atnf.csiro.au": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:17:08 [FAIL] ‹http://sebastian.network› with ‹Get "http://sebastian.network": EOF›
2024/07/16 13:17:13 [FAIL] ‹http://math.lbl.gov› with ‹Get "https://crd.lbl.gov/divisions/amcr/mathematics-dept/math/members/": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:17:18 [FAIL] ‹https://multiprecision.org› with ‹Get "https://multiprecision.org": dial tcp: lookup multiprecision.org: no such host›
2024/07/16 13:17:18 [FAIL] ‹http://vim.org› with ‹Get "http://vim.org": dial tcp: lookup vim.org: no such host›
2024/07/16 13:17:31 [FAIL] ‹http://and.org› with ‹Get "http://and.org": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:17:32 [FAIL] ‹http://hokuyo-aut.jp› with ‹Get "http://hokuyo-aut.jp": dial tcp: lookup hokuyo-aut.jp: no such host›
2024/07/16 13:17:37 [FAIL] ‹http://archives.math.utk.edu› with ‹Get "http://archives.math.utk.edu": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:17:38 [FAIL] ‹http://unixodbc.org› with ‹Get "http://unixodbc.org": dial tcp: lookup unixodbc.org: no such host›
2024/07/16 13:17:43 [FAIL] ‹http://geocities.jp› with ‹Get "http://geocities.jp": dial tcp: lookup geocities.jp: no such host›
2024/07/16 13:17:46 [FAIL] ‹https://urlfilterdb.com› with ‹Get "https://urlfilterdb.com": dial tcp 188.40.204.242:443: connect: no route to host›
2024/07/16 13:17:52 [FAIL] ‹http://tzclock.org› with ‹Get "https://tzclock.org/": tls: failed to verify certificate: x509: certificate is valid for theknight.co.uk, www.theknight.co.uk, not tzclock.org›
2024/07/16 13:17:55 [FAIL] ‹http://wa0eir.bcts.info› with ‹Get "http://wa0eir.bcts.info": dial tcp: lookup wa0eir.bcts.info: no such host›
2024/07/16 13:17:55 [FAIL] ‹http://efd.lth.se› with ‹Get "http://efd.lth.se": dial tcp: lookup efd.lth.se: no such host›
2024/07/16 13:17:55 [FAIL] ‹http://download.tuxanci.org› with ‹Get "http://download.tuxanci.org": dial tcp: lookup download.tuxanci.org: no such host›
2024/07/16 13:18:04 [FAIL] ‹https://mama.indstate.edu› with ‹Get "https://mama.indstate.edu": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:18:14 [FAIL] ‹http://tntnet.org› with ‹Get "http://tntnet.org": dial tcp 185.89.197.101:80: connect: connection refused›
2024/07/16 13:18:14 [FAIL] ‹http://tiptop.gforge.inria.fr› with ‹Get "http://tiptop.gforge.inria.fr": dial tcp: lookup tiptop.gforge.inria.fr: no such host›
2024/07/16 13:18:17 [FAIL] ‹http://efeu.cybertec.at› with ‹Get "http://efeu.cybertec.at": dial tcp: lookup efeu.cybertec.at: no such host›
2024/07/16 13:18:20 [FAIL] ‹http://personal.utulsa.edu› with ‹Get "http://personal.utulsa.edu": dial tcp: lookup personal.utulsa.edu: no such host›
2024/07/16 13:18:22 [FAIL] ‹http://remlab.net› with ‹Get "http://remlab.net": dial tcp: lookup remlab.net: no such host›
2024/07/16 13:18:30 [FAIL] ‹http://tcpcrypt.org› with ‹Get "http://tcpcrypt.org": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:18:36 [FAIL] ‹http://download.banshee-project.org› with ‹Get "http://download.banshee-project.org": dial tcp: lookup download.banshee-project.org: no such host›
2024/07/16 13:18:36 [FAIL] ‹http://kollide.net› with ‹Get "http://kollide.net": dial tcp 127.0.0.1:80: connect: connection refused›
2024/07/16 13:18:40 [FAIL] ‹http://math.uni-rostock.de› with ‹Get "http://math.uni-rostock.de": dial tcp: lookup math.uni-rostock.de: no such host›
2024/07/16 13:18:44 [FAIL] ‹http://surfraw.alioth.debian.org› with ‹Get "http://surfraw.alioth.debian.org": dial tcp: lookup surfraw.alioth.debian.org: no such host›
2024/07/16 13:18:53 [FAIL] ‹http://cuda.port-aransas.k12.tx.us› with ‹Get "http://cuda.port-aransas.k12.tx.us": dial tcp: lookup cuda.port-aransas.k12.tx.us: no such host›
2024/07/16 13:18:58 [FAIL] ‹http://squidguard.mesd.k12.or.us› with ‹Get "http://squidguard.mesd.k12.or.us": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:19:03 [FAIL] ‹http://squidguard.org› with ‹Get "http://squidguard.org": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:19:10 [FAIL] ‹http://dest-unreach.org› with ‹Get "http://dest-unreach.org": dial tcp: lookup dest-unreach.org: no such host›
2024/07/16 13:19:15 [FAIL] ‹http://download.sinenomine.net› with ‹Get "http://download.sinenomine.net": dial tcp 198.44.193.24:80: connect: no route to host›
2024/07/16 13:19:27 [FAIL] ‹https://ymu.dl.osdn.jp› with ‹Get "http://osdn.jp/": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:19:33 [FAIL] ‹http://six.retes.hu› with ‹Get "http://six.retes.hu": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:19:38 [FAIL] ‹http://freequaos.host.sk› with ‹Get "https://freequaos.host.sk/": tls: failed to verify certificate: x509: certificate has expired or is not yet valid: current time 2024-07-16T13:19:38+02:00 is after 2024-06-10T23:25:23Z›
2024/07/16 13:19:44 [FAIL] ‹http://etree.org› with ‹Get "http://etree.org": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:20:02 [FAIL] ‹http://globalbase.dl.sourceforge.jp› with ‹Get "http://globalbase.dl.sourceforge.jp": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:20:05 [FAIL] ‹http://ftp.linux.org.uk› with ‹Get "http://ftp.linux.org.uk": dial tcp 62.89.141.173:80: connect: connection refused›
2024/07/16 13:20:10 [FAIL] ‹https://cutter.osdn.jp› with ‹Get "https://cutter.osdn.jp": dial tcp 52.32.250.235:443: i/o timeout›
2024/07/16 13:20:14 [FAIL] ‹http://rafalab.jhsph.edu› with ‹Get "https://rafalab.jhsph.edu/": tls: failed to verify certificate: x509: certificate is valid for biostat.jhsph.edu, biosun01.biostat.jhsph.edu, www.biostat.jhsph.edu, not rafalab.jhsph.edu›
2024/07/16 13:20:19 [FAIL] ‹http://tecgraf.puc-rio.br› with ‹Get "https://www.tecgraf.puc-rio.br/": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:20:22 [FAIL] ‹https://ricochet.im› with ‹Get "https://ricochet.im": dial tcp: lookup ricochet.im: no such host›
2024/07/16 13:20:30 [FAIL] ‹http://infradead.org› with ‹Get "http://infradead.org": dial tcp: lookup infradead.org: no such host›
2024/07/16 13:20:42 [FAIL] ‹http://buttari.perso.enseeiht.fr› with ‹Get "http://buttari.perso.enseeiht.fr": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:20:50 [FAIL] ‹http://home.kpn.nl› with ‹Get "http://home.kpn.nl": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:20:58 [FAIL] ‹http://code.liw.fi› with ‹Get "http://code.liw.fi": dial tcp: lookup code.liw.fi: no such host›
2024/07/16 13:21:06 [FAIL] ‹http://alcyone.com› with ‹Get "http://alcyone.com": dial tcp: lookup alcyone.com: no such host›
2024/07/16 13:21:10 [FAIL] ‹http://deron.meranda.us› with ‹Get "http://deron.meranda.us": dial tcp 66.117.209.18:80: connect: no route to host›
2024/07/16 13:21:18 [FAIL] ‹http://nsd.dyndns.org› with ‹Get "http://nsd.dyndns.org": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:21:42 [FAIL] ‹https://users.cecs.anu.edu.au› with ‹Get "https://users.cecs.anu.edu.au////": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:21:47 [FAIL] ‹http://planets.homedns.org› with ‹Get "http://planets.homedns.org": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:21:49 [FAIL] ‹http://users.waitrose.com› with ‹Get "http://users.waitrose.com": dial tcp: lookup users.waitrose.com: no such host›
2024/07/16 13:21:51 [FAIL] ‹http://downloads.guifications.org› with ‹Get "http://downloads.guifications.org": dial tcp: lookup downloads.guifications.org: no such host›
2024/07/16 13:21:52 [FAIL] ‹http://phpsmug.com› with ‹Get "http://phpsmug.com": dial tcp: lookup phpsmug.com: no such host›
2024/07/16 13:21:55 [FAIL] ‹http://bitfolge.de› with ‹Get "https://wwww.elato.media/": dial tcp: lookup wwww.elato.media: no such host›
2024/07/16 13:21:55 [FAIL] ‹httpd://pecl.php.net› with ‹Get "httpd://pecl.php.net": unsupported protocol scheme "httpd"›
2024/07/16 13:22:07 [FAIL] ‹http://wiki.servicenow.com› with ‹Get "http://wiki.servicenow.com": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:22:13 [FAIL] ‹http://laqee.unal.edu.co› with ‹Get "http://laqee.unal.edu.co": dial tcp: lookup laqee.unal.edu.co: no such host›
2024/07/16 13:22:33 [FAIL] ‹http://leandro.iqm.unicamp.br› with ‹Get "http://leandro.iqm.unicamp.br": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:22:38 [FAIL] ‹http://sofia.nmsu.edu› with ‹Get "http://sofia.nmsu.edu": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:22:44 [FAIL] ‹http://old.openzwave.com› with ‹Get "http://old.openzwave.com": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:22:44 [FAIL] ‹https://openvswitch.org› with ‹Get "https://openvswitch.org": tls: failed to verify certificate: x509: certificate is valid for *.dnsmadeeasy.com, not openvswitch.org›
2024/07/16 13:22:56 [FAIL] ‹http://hg.openjdk.java.net› with ‹Get "http://hg.openjdk.java.net": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:23:07 [FAIL] ‹http://scienzaludica.it› with ‹Get "http://scienzaludica.it": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:23:09 [FAIL] ‹http://ant.uni-bremen.de› with ‹Get "http://ant.uni-bremen.de": dial tcp: lookup ant.uni-bremen.de: no such host›
2024/07/16 13:23:14 [FAIL] ‹http://eecis.udel.edu› with ‹Get "http://eecis.udel.edu": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:23:27 [FAIL] ‹http://nmbscan.g76r.eu› with ‹Get "http://nmbscan.g76r.eu": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:23:42 [FAIL] ‹http://tweegy.nl› with ‹Get "http://tweegy.nl": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:23:44 [FAIL] ‹http://downloads.usrsrc.org› with ‹Get "http://downloads.usrsrc.org": dial tcp: lookup downloads.usrsrc.org: no such host›
2024/07/16 13:23:45 [FAIL] ‹http://central.maven.org› with ‹Get "http://central.maven.org": dial tcp: lookup central.maven.org: no such host›
2024/07/16 13:23:50 [FAIL] ‹httip://downloads.sourceforge.net› with ‹Get "httip://downloads.sourceforge.net": unsupported protocol scheme "httip"›
2024/07/16 13:24:03 [FAIL] ‹http://littlehat.homelinux.org› with ‹Get "http://littlehat.homelinux.org": dial tcp: lookup littlehat.homelinux.org: no such host›
2024/07/16 13:24:07 [FAIL] ‹https://mpfr.org› with ‹Get "https://mpfr.org": tls: failed to verify certificate: x509: certificate is valid for mpfr.loria.fr, www.mpfr.org, not mpfr.org›
2024/07/16 13:24:08 [FAIL] ‹http://bytereef.org› with ‹Get "http://bytereef.org": dial tcp: lookup bytereef.org: no such host›
2024/07/16 13:24:17 [FAIL] ‹https://mod.gnutls.org› with ‹Get "https://mod.gnutls.org": dial tcp 209.51.180.251:443: connect: no route to host›
2024/07/16 13:24:20 [FAIL] ‹http://ivn.cl› with ‹Get "https://wp.ivn.cl": tls: failed to verify certificate: x509: certificate signed by unknown authority›
2024/07/16 13:24:22 [FAIL] ‹http://staff.science.uu.nl› with ‹Get "http://staff.science.uu.nl": dial tcp: lookup staff.science.uu.nl: no such host›
2024/07/16 13:24:37 [FAIL] ‹http://forkosh.com› with ‹Get "http://116.179.37.45/": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:24:38 [FAIL] ‹https://ftp.freedesktop.org› with ‹Get "https://ftp.freedesktop.org": tls: failed to verify certificate: x509: certificate is valid for distributions.freedesktop.org, farsight.freedesktop.org, fontconfig.freedesktop.org, fontconfig.org, freedesktop.org, geoclue.freedesktop.org, secure.freedesktop.org, www.fontconfig.org, www.freedesktop.org, not ftp.freedesktop.org›
2024/07/16 13:24:46 [FAIL] ‹http://jipdec.or.jp› with ‹Get "https://jipdec.or.jp/": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:24:52 [FAIL] ‹http://starship.python.net› with ‹Get "http://starship.python.net": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:24:57 [FAIL] ‹http://primates.ximian.com› with ‹Get "http://primates.ximian.com": dial tcp: lookup primates.ximian.com: no such host›
2024/07/16 13:25:02 [FAIL] ‹http://linuxjm.osdn.jp› with ‹Get "http://linuxjm.osdn.jp": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:25:07 [FAIL] ‹http://home.arcor.de› with ‹Get "http://home.arcor.de": dial tcp: lookup home.arcor.de: no such host›
2024/07/16 13:25:16 [FAIL] ‹https://faculty.math.illinois.edu› with ‹Get "https://faculty.math.illinois.edu": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:25:21 [FAIL] ‹http://faculty.math.illinois.edu› with ‹Get "http://faculty.math.illinois.edu": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:25:25 [FAIL] ‹http://ff.iij4u.or.jp› with ‹Get "http://ff.iij4u.or.jp": dial tcp: lookup ff.iij4u.or.jp: no such host›
2024/07/16 13:25:35 [FAIL] ‹http://luaforge.net› with ‹Get "http://luaforge.net": EOF›
2024/07/16 13:25:52 [FAIL] ‹http://ssisc.org› with ‹Get "http://ssisc.org": dial tcp: lookup ssisc.org: no such host›
2024/07/16 13:25:55 [FAIL] ‹http://seasip.demon.co.uk› with ‹Get "http://seasip.demon.co.uk": dial tcp: lookup seasip.demon.co.uk: no such host›
2024/07/16 13:25:57 [FAIL] ‹http://download.boulder.ibm.com› with ‹Get "http://download.boulder.ibm.com": dial tcp 170.225.126.19:80: connect: connection refused›
2024/07/16 13:25:59 [FAIL] ‹https://leonerd.org.uk› with ‹Get "https://leonerd.org.uk": dial tcp: lookup leonerd.org.uk: no such host›
2024/07/16 13:26:03 [FAIL] ‹https://pages.stern.nyu.edu› with ‹Get "https://pages.stern.nyu.edu": tls: failed to verify certificate: x509: certificate signed by unknown authority›
2024/07/16 13:26:03 [FAIL] ‹http://du-a.org› with ‹Get "http://du-a.org": dial tcp: lookup du-a.org: no such host›
2024/07/16 13:26:04 [FAIL] ‹http://leonerd.org.uk› with ‹Get "http://leonerd.org.uk": dial tcp: lookup leonerd.org.uk: no such host›
2024/07/16 13:26:15 [FAIL] ‹http://vrt.com.au› with ‹Get "https://vrt.com.au/": tls: failed to verify certificate: x509: certificate is valid for www.vrt.com.au, not vrt.com.au›
2024/07/16 13:26:15 [FAIL] ‹http://dside.dyndns.org› with ‹Get "http://dside.dyndns.org": dial tcp: lookup dside.dyndns.org: no such host›
2024/07/16 13:26:18 [FAIL] ‹http://five-ten-sg.com› with ‹Get "http://five-ten-sg.com": dial tcp: lookup five-ten-sg.com: no such host›
2024/07/16 13:26:26 [FAIL] ‹https://git.merproject.org› with ‹Get "https://git.merproject.org": dial tcp: lookup git.merproject.org: no such host›
2024/07/16 13:26:28 [FAIL] ‹http://projects.o-hand.com› with ‹Get "http://projects.o-hand.com": dial tcp: lookup projects.o-hand.com: no such host›
2024/07/16 13:26:30 [FAIL] ‹http://liblognorm.com› with ‹Get "http://liblognorm.com": dial tcp: lookup liblognorm.com: no such host›
2024/07/16 13:26:35 [FAIL] ‹http://stafford.uklinux.net› with ‹Get "http://stafford.uklinux.net": dial tcp: lookup stafford.uklinux.net: no such host›
2024/07/16 13:26:36 [FAIL] ‹http://files.lfranchi.com› with ‹Get "http://files.lfranchi.com": dial tcp: lookup files.lfranchi.com: no such host›
2024/07/16 13:26:46 [FAIL] ‹http://ics.forth.gr› with ‹Get "https://ics.forth.gr/": tls: failed to verify certificate: x509: certificate signed by unknown authority›
2024/07/16 13:26:49 [FAIL] ‹http://lichteblau.com› with ‹Get "http://lichteblau.com": dial tcp: lookup lichteblau.com: no such host›
2024/07/16 13:26:49 [FAIL] ‹http://archive.lbzip2.org› with ‹Get "http://archive.lbzip2.org": dial tcp: lookup archive.lbzip2.org: no such host›
2024/07/16 13:27:01 [FAIL] ‹https://laf-plugin.dev.java.net› with ‹Get "https://laf-plugin.dev.java.net": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:27:07 [FAIL] ‹http://home.planet.nl› with ‹Get "http://home.planet.nl": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:27:09 [FAIL] ‹https://gitorious.org› with ‹Get "https://gitorious.org": tls: failed to verify certificate: x509: certificate has expired or is not yet valid: current time 2024-07-16T13:27:09+02:00 is after 2019-03-28T19:44:58Z›
2024/07/16 13:27:23 [FAIL] ‹http://jaist.dl.sourceforge.jp› with ‹Get "http://jaist.dl.sourceforge.jp": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:27:24 [FAIL] ‹http://jxrlib.codeplex.com› with ‹Get "http://jxrlib.codeplex.com": dial tcp: lookup jxrlib.codeplex.com: no such host›
2024/07/16 13:27:25 [FAIL] ‹http://math.union.edu› with ‹Get "http://math.union.edu": dial tcp: lookup math.union.edu: no such host›
2024/07/16 13:27:28 [FAIL] ‹http://jcraft.com› with ‹Get "http://jcraft.com": dial tcp: lookup jcraft.com: no such host›
2024/07/16 13:27:38 [FAIL] ‹http://kappa.allnet.ne.jp› with ‹Get "http://kappa.allnet.ne.jp": dial tcp 61.211.150.156:80: i/o timeout (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:27:43 [FAIL] ‹http://dl.ivtvdriver.org› with ‹Get "https://dl.ivtvdriver.org/": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:27:54 [FAIL] ‹https://rsb.info.nih.gov› with ‹Get "https://rsb.info.nih.gov": tls: failed to verify certificate: x509: certificate is valid for imagej.nih.gov, not rsb.info.nih.gov›
2024/07/16 13:27:54 [FAIL] ‹https://rsbweb.nih.gov› with ‹Get "https://rsbweb.nih.gov": tls: failed to verify certificate: x509: certificate is valid for imagej.nih.gov, not rsbweb.nih.gov›
2024/07/16 13:27:59 [FAIL] ‹http://crash.ihug.co.nz› with ‹Get "http://crash.ihug.co.nz": dial tcp: lookup crash.ihug.co.nz: no such host›
2024/07/16 13:28:02 [FAIL] ‹http://chocolate-doom.org› with ‹Get "http://chocolate-doom.org": dial tcp: lookup chocolate-doom.org: no such host›
2024/07/16 13:28:07 [FAIL] ‹http://jedrea.com› with ‹Get "http://jedrea.com": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:28:10 [FAIL] ‹https://forxa.mancomun.org› with ‹Get "https://forxa.mancomun.org": dial tcp: lookup forxa.mancomun.org: no such host›
2024/07/16 13:28:18 [FAIL] ‹http://lin.fsid.cvut.cz› with ‹Get "http://lin.fsid.cvut.cz": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:28:24 [FAIL] ‹http://www-user.uni-bremen.de› with ‹Get "http://www-user.uni-bremen.de": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:28:36 [FAIL] ‹http://borel.slu.edu› with ‹Get "http://borel.slu.edu": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:28:46 [FAIL] ‹http://da.speling.org› with ‹Get "http://da.speling.org": dial tcp: lookup da.speling.org: no such host›
2024/07/16 13:28:51 [FAIL] ‹http://downloads.translate.org.za› with ‹Get "http://downloads.translate.org.za": dial tcp: lookup downloads.translate.org.za: no such host›
2024/07/16 13:29:00 [FAIL] ‹https://osdn.jp› with ‹Get "https://osdn.jp": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:29:03 [FAIL] ‹http://download.logilab.org› with ‹Get "http://download.logilab.org": dial tcp: lookup download.logilab.org: no such host›
2024/07/16 13:29:04 [FAIL] ‹http://jacobdekel.com› with ‹Get "http://jacobdekel.com": dial tcp: lookup jacobdekel.com: no such host›
2024/07/16 13:29:14 [FAIL] ‹http://ja.osdn.net› with ‹Get "http://ja.osdn.net": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:29:16 [FAIL] ‹http://guitone.thomaskeller.biz› with ‹Get "http://guitone.thomaskeller.biz": dial tcp: lookup guitone.thomaskeller.biz: no such host›
2024/07/16 13:29:26 [FAIL] ‹http://download.ecmwf.org› with ‹Get "http://download.ecmwf.org": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:29:31 [FAIL] ‹https://software.ecmwf.int› with ‹Get "https://software.ecmwf.int": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:29:40 [FAIL] ‹http://ncc.up.pt› with ‹Get "http://ncc.up.pt": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:29:40 [FAIL] ‹https://imagination-land.org› with ‹Get "https://imagination-land.org": dial tcp 217.70.184.38:443: connect: connection refused›
2024/07/16 13:29:41 [FAIL] ‹https://git.schwanenlied.me› with ‹Get "https://git.schwanenlied.me": dial tcp: lookup git.schwanenlied.me: no such host›
2024/07/16 13:30:01 [FAIL] ‹http://some-gimp-plugins.com› with ‹Get "http://ww1.some-gimp-plugins.com": EOF›
2024/07/16 13:30:03 [FAIL] ‹http://asgaard.homelinux.org› with ‹Get "http://asgaard.homelinux.org": dial tcp: lookup asgaard.homelinux.org: no such host›
2024/07/16 13:30:11 [FAIL] ‹http://mirror.vocabbuilder.net› with ‹Get "http://mirror.vocabbuilder.net": dial tcp: lookup mirror.vocabbuilder.net: no such host›
2024/07/16 13:30:11 [FAIL] ‹http://icm.tu-bs.de› with ‹Get "http://icm.tu-bs.de": dial tcp: lookup icm.tu-bs.de: no such host›
2024/07/16 13:30:12 [FAIL] ‹http://iro.umontreal.ca› with ‹Get "http://iro.umontreal.ca": dial tcp: lookup iro.umontreal.ca: no such host›
2024/07/16 13:30:14 [FAIL] ‹http://funionfs.apiou.org› with ‹Get "http://funionfs.apiou.org": dial tcp: lookup funionfs.apiou.org: no such host›
2024/07/16 13:30:14 [FAIL] ‹http://dsm.fordham.edu› with ‹Get "http://dsm.fordham.edu": dial tcp: lookup dsm.fordham.edu: no such host›
2024/07/16 13:30:21 [FAIL] ‹http://frozen-bubble.org› with ‹Get "http://frozen-bubble.org": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:30:22 [FAIL] ‹https://freetds.org› with ‹Get "https://freetds.org": dial tcp: lookup freetds.org: no such host›
2024/07/16 13:30:27 [FAIL] ‹http://mumps.enseeiht.fr› with ‹Get "http://mumps.enseeiht.fr": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:30:32 [FAIL] ‹http://freediameter.net› with ‹Get "http://freediameter.net": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:30:51 [FAIL] ‹https://nongnu.org› with ‹Get "https://www.nongnu.org/": tls: failed to verify certificate: x509: certificate has expired or is not yet valid: current time 2024-07-16T13:30:51+02:00 is after 2024-07-16T05:43:15Z›
2024/07/16 13:30:55 [FAIL] ‹http://fastcgi.com› with ‹Get "http://fastcgi.com": dial tcp 216.213.99.150:80: connect: network is unreachable›
2024/07/16 13:30:55 [FAIL] ‹https://kraxel.org› with ‹Get "https://kraxel.org": tls: failed to verify certificate: x509: certificate is valid for hagrid.kraxel.org, not kraxel.org›
2024/07/16 13:31:08 [FAIL] ‹http://academicunderground.org› with ‹Get "http://academicunderground.org": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:31:13 [FAIL] ‹http://balabit.com› with ‹Get "https://oneIdentity.com": remote error: tls: internal error›
2024/07/16 13:31:14 [FAIL] ‹http://mirror.cs.wisc.edu› with ‹Get "http://mirror.cs.wisc.edu": dial tcp: lookup mirror.cs.wisc.edu: no such host›
2024/07/16 13:31:16 [FAIL] ‹http://spice-mode.4t.com› with ‹Get "http://spice-mode.4t.com": dial tcp: lookup spice-mode.4t.com: no such host›
2024/07/16 13:31:18 [FAIL] ‹http://fly.srk.fer.hr› with ‹Get "http://fly.srk.fer.hr": dial tcp: lookup fly.srk.fer.hr: no such host›
2024/07/16 13:31:30 [FAIL] ‹http://opendx.informatics.jax.org› with ‹Get "http://opendx.informatics.jax.org": dial tcp: lookup opendx.informatics.jax.org: no such host›
2024/07/16 13:31:33 [FAIL] ‹http://dvdisaster.net› with ‹Get "http://dvdisaster.net": dial tcp: lookup dvdisaster.net: no such host›
2024/07/16 13:31:44 [FAIL] ‹https://mcs.anl.gov› with ‹Get "https://mcs.anl.gov": dial tcp: lookup mcs.anl.gov: no such host›
2024/07/16 13:31:46 [FAIL] ‹http://documentation.ofset.org› with ‹Get "http://documentation.ofset.org": dial tcp: lookup documentation.ofset.org: no such host›
2024/07/16 13:31:54 [FAIL] ‹http://dirvish.org› with ‹Get "https://dirvish.org/": tls: failed to verify certificate: x509: certificate signed by unknown authority›
2024/07/16 13:32:00 [FAIL] ‹https://dillo.org› with ‹Get "https://dillo.org": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:32:05 [FAIL] ‹http://mangrove.cz› with ‹Get "http://mangrove.cz": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:32:05 [FAIL] ‹https://fefe.de› with ‹Get "https://fefe.de": dial tcp: lookup fefe.de: no such host›
2024/07/16 13:32:07 [FAIL] ‹http://v3.sk› with ‹Get "https://v3.sk/": http: server gave HTTP response to HTTPS client›
2024/07/16 13:32:08 [FAIL] ‹http://kalysto.org› with ‹Get "https://kalysto.org/": tls: failed to verify certificate: x509: certificate has expired or is not yet valid: current time 2024-07-16T13:32:08+02:00 is after 2023-02-26T19:18:57Z›
2024/07/16 13:32:14 [FAIL] ‹https://inet.no› with ‹Get "https://inet.no": dial tcp: lookup inet.no: no such host›
2024/07/16 13:32:17 [FAIL] ‹http://cobite.com› with ‹Get "http://cobite.com": dial tcp: lookup cobite.com: no such host›
2024/07/16 13:32:17 [FAIL] ‹https://cups-pdf.de› with ‹Get "https://cups-pdf.de": dial tcp: lookup cups-pdf.de: no such host›
2024/07/16 13:32:18 [FAIL] ‹http://cons.org› with ‹Get "https://cons.org/": tls: failed to verify certificate: x509: certificate is valid for koef.zs64.net, not cons.org›
2024/07/16 13:32:23 [FAIL] ‹http://creativecommons.org› with ‹Get "http://creativecommons.org": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:32:28 [FAIL] ‹http://cronolog.org› with ‹Get "http://cronolog.org": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:32:38 [FAIL] ‹http://agroman.net› with ‹Get "http://agroman.net": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:32:48 [FAIL] ‹http://comicneue.com› with ‹Get "http://comicneue.com": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:32:50 [FAIL] ‹http://pg4i.chronos.org.uk› with ‹Get "http://pg4i.chronos.org.uk": dial tcp: lookup pg4i.chronos.org.uk: no such host›
2024/07/16 13:32:50 [FAIL] ‹http://colordiff.org› with ‹Get "https://colordiff.org/": tls: failed to verify certificate: x509: certificate is valid for www.colordiff.org, not colordiff.org›
2024/07/16 13:33:04 [FAIL] ‹http://bofh.it› with ‹Get "http://bofh.it": dial tcp: lookup bofh.it: no such host›
2024/07/16 13:33:14 [FAIL] ‹http://cdrkit.org› with ‹Get "http://cdrkit.org": dial tcp: lookup cdrkit.org: no such host›
2024/07/16 13:33:25 [FAIL] ‹http://campivisivi.net› with ‹Get "http://www.campivisivi.net/": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:33:30 [FAIL] ‹http://andywilcock.com› with ‹Get "http://andywilcock.com": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:33:31 [FAIL] ‹https://imcce.fr› with ‹Get "https://imcce.fr": dial tcp: lookup imcce.fr: no such host›
2024/07/16 13:33:32 [FAIL] ‹http://ing.unibs.it› with ‹Get "http://ing.unibs.it": dial tcp: lookup ing.unibs.it: no such host›
2024/07/16 13:33:39 [FAIL] ‹http://busybox.net› with ‹Get "https://busybox.net/": context deadline exceeded (Client.Timeout exceeded while awaiting headers)›
2024/07/16 13:33:40 [FAIL] ‹http://ne.jp› with ‹Get "http://ne.jp": dial tcp: lookup ne.jp: no such host›
2024/07/16 13:33:52 [FAIL] ‹http://bitchx.ca› with ‹Get "http://bitchx.ca": EOF›
2024/07/16 13:33:55 [FAIL] ‹http://gnu.ethz.ch› with ‹Get "http://gnu.ethz.ch": dial tcp: lookup gnu.ethz.ch: no such host›
2024/07/16 13:33:59 [FAIL] ‹https://beansbinding.dev.java.net› with ‹Get "https://beansbinding.dev.java.net": dial tcp 137.254.56.48:443: connect: network is unreachable›
2024/07/16 13:34:07 [FAIL] ‹https://harding.motd.ca› with ‹Get "https://harding.motd.ca": dial tcp: lookup harding.motd.ca: no such host›
2024/07/16 13:34:13 [FAIL] ‹http://starlink.ac.uk› with ‹Get "http://starlink.ac.uk": dial tcp: lookup starlink.ac.uk: no such host›
2024/07/16 13:34:18 [FAIL] ‹http://cybernoia.de› with ‹Get "https://cybernoia.de/": tls: failed to verify certificate: x509: certificate has expired or is not yet valid: current time 2024-07-16T13:34:18+02:00 is after 2022-09-23T14:37:42Z›
2024/07/16 13:34:21 [FAIL] ‹http://adel.nursat.kz› with ‹Get "http://adel.nursat.kz": dial tcp: lookup adel.nursat.kz: no such host›
2024/07/16 13:34:26 [FAIL] ‹http://repo2.maven.org› with ‹Get "http://repo2.maven.org": dial tcp: lookup repo2.maven.org: no such host›
2024/07/16 13:34:26 [FAIL] ‹http://winfield.demon.nl› with ‹Get "http://winfield.demon.nl": dial tcp: lookup winfield.demon.nl: no such host›
2024/07/16 13:34:32 [FAIL] ‹http://kcat.strangesoft.net› with ‹Get "http://kcat.strangesoft.net": dial tcp: lookup kcat.strangesoft.net: no such host›
2024/07/16 13:34:40 [FAIL] ‹https://ahven-framework.com› with ‹Get "https://ahven-framework.com": tls: failed to verify certificate: x509: certificate is valid for www.ahven-framework.com, not ahven-framework.com›
```

</details>

### How to reproduce

Rather brief description of how to reproduce follows.

#### Obtaining the sources

Provided by @xsuchy

```bash
for i in *spec; do
    spectool $i |grep Source
done >/tmp/output.txt
```

Additionally gzip-compressed.

#### Processing the sources

```bash
python3 process.py ‹path to the gzip-compressed scraped sources›
```

#### Running the checker of domains

Expects the list of domains in format `http(s)://domain.tld` in file
`domains.txt` in a parent directory of the directory where the `checker.go` is
being run from.

```bash
go run checker.go 2> log.txt
```

`log.txt` contains the logging messages, `stdout` progress bar.
