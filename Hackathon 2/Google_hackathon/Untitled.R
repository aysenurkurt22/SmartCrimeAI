# data cleaning

df=read.csv("/Users/aman/coding stuff/google cpptonight/train_f.csv",header=TRUE)
df
lf=read.csv("/Users/aman/coding stuff/google cpptonight/test_raw.csv/test.csv",header=TRUE)
df[ , colSums(is.na(df)/nrow(df)) < 0.50]
subset(df, select=-c('country_id','city_id','org_id','geo_id','local_name_id','processor','smart_screen','name_id','model_id','core_count_processer','model_id.1','disk_capacity','disk_type','system_voulme_capacity','has_optical_drive','ram_capacity','chassis_type','diagonal_display_size','display_resolution_horizontal','display_resolution_vertical','battery_type','number_of_charges_of_battery','build_number','is_gamer','age','sex'))

df_coldel=df[ , -which(names(df) %in% c('country_id','win_boot_status','threshold_choice','flighting_status','number_of_charges_for_battery','default_browser','org_id','city_id','org_id','geo_id','local_name_id','processor','smart_screen','name_id','model_id','core_count_processer','model_id.1','disk_capacity','disk_type','system_voulme_capacity','has_optical_drive','ram_capacity','chassis_type','diagonal_display_size','display_resolution_horizontal','display_resolution_vertical','battery_type','number_of_charges_of_battery','build_number','is_gamer','age','sex'))]


colSums(is.na(df_coldel))
df_coldel=df_coldel[,-which(names(df_coldel) %in% c('wim_boot_status','firmware_manufacturer_id','region_id','s_mode','flights_activity','firmware_version_id','firewall'))]


df_coldel=df_coldel[,-which(names(df_coldel) %in% c('pen_support','aoac_support','touch_support','av_sig_version','processor_class','system_volume_capacity','os_ptfm_sub_release','state_name','install_language_identifier','install_type_name','mdc2_form_factor','uac_luaenable','power_profile'))]
colSums(is.na(df_coldel))

#df_coldel=df_coldel[,-which(names(df_coldel) %in% c('security_product_name','rtp_state','edition','os_build','sku_edition','os_version','version','architecture','branch','build_revision','sku','os_suite','av_prod_enabled','av_prod_installed','virtual_dev_status','activation_channel','platform','os_type_status'))]
#colSums(is.na(df_coldel))

##############################

lf_coldel=lf[ , -which(names(lf) %in% c('country_id','win_boot_status','threshold_choice','flighting_status','number_of_charges_for_battery','default_browser','org_id','city_id','org_id','geo_id','local_name_id','processor','smart_screen','name_id','model_id','core_count_processer','model_id.1','disk_capacity','disk_type','system_voulme_capacity','has_optical_drive','ram_capacity','chassis_type','diagonal_display_size','display_resolution_horizontal','display_resolution_vertical','battery_type','number_of_charges_of_battery','build_number','is_gamer','age','sex'))]


colSums(is.na(lf_coldel))
lf_coldel=lf_coldel[,-which(names(lf_coldel) %in% c('wim_boot_status','firmware_manufacturer_id','region_id','s_mode','flights_activity','firmware_version_id','firewall'))]


lf_coldel=lf_coldel[,-which(names(lf_coldel) %in% c('pen_support','aoac_support','touch_support','av_sig_version','processor_class','system_volume_capacity','os_ptfm_sub_release','state_name','install_language_identifier','install_type_name','mdc2_form_factor','uac_luaenable','power_profile'))]
colSums(is.na(lf_coldel))

#lf_coldel=lf_coldel[,-which(names(lf_coldel) %in% c('security_product_name','rtp_state','edition','os_build','sku_edition','os_version','version','architecture','branch','build_revision','sku','os_suite','av_prod_enabled','av_prod_installed','virtual_dev_status','activation_channel','platform','os_type_status'))]
#colSums(is.na(lf_coldel))

table(df_coldel$auto_sample_opt_in)

install.packages("MCA")

install.packages('naniar')
install.packages('FactoMineR')
install.packages('missMDA')
install.packages('denoiseR')
install.packages('Hmisc')
library(Hmisc)
library(naniar)
library(VIM)
library(FactoMineR)
library(missMDA)
gg_miss_var(lf_coldel)

res<-summary(aggr(lf_coldel, sortVar=TRUE))$combinations
install.packages('imputeMCA')

library(denoiseR)
data(impactfactor)
summary(impactfactor)


imputeMCA(df_coldel, ncp=2, method = c("Regularized","EM"), row.w=NULL, coeff.ridge=1, 
          threshold=1e-06, ind.sup = NULL, quanti.sup=NULL, quali.sup=NULL,
          seed=NULL, maxiter=1000)

res.imp <- imputeMFA(impactfactor,  group = rep(3, 15),  type = rep("s", 15))

## MFA on the imputed data set
res.mfa  <-MFA(res.imp$completeObs, group=rep(3,15),  type=rep("s",15), 
               name.group=paste("year", 1999:2013,sep="_"),graph=F)


colSums(is.na(df_coldel))
impute(df_coldel$rtp_state ,mode)
impute(df_coldel$av_status ,mode)
impute(df_coldel$av_prod_installed ,mode)
impute(df_coldel$av_prod_enabled ,mode)
impute(df_coldel$is_protected ,mode)
impute(df_coldel$ie_ver_id ,mode)
impute(df_coldel$firewall ,mode)



colSums(is.na(df_coldel))
impute(lf_coldel$rtp_state ,mode)
impute(lf_coldel$av_status ,mode)
impute(lf_coldel$av_prod_installed ,mode)
impute(lf_coldel$av_prod_enabled ,mode)
impute(lf_coldel$is_protected ,mode)
impute(lf_coldel$ie_ver_id ,mode)
impute(lf_coldel$firewall ,mode)


library("mice")
imp <- mice(df_coldel, m = 1)
# m = 1 specifies a single imputation, standard would be m = 5 for multiple imputation


# Completed data
data_imp <- complete(imp)
data_imp

colSums(is.na(data_imp))


average_missing <- apply(df_coldel[,colnames(df_coldel) %in% list_na],
                         2,
                         mode,
                         na.rm =  TRUE)




df_titanic_impute_mean < -data.frame(sapply(df_coldel,function(x) ifelse(is.na(x),mode(x, na.rm = TRUE),x)))



write.csv(df_coldel,"/Users/aman/coding stuff/google cpptonight/train_fi.csv", row.names = FALSE)

write.csv(lf_coldel,"/Users/aman/coding stuff/google cpptonight/test_fi.csv", row.names = FALSE)
lf_coldel
